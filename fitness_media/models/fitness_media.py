import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessMedia(models.Model):
    _name = "fitness.media"
    _description = "Fitness Media"
    _order = "is_primary desc, id desc"

    MEDIA_KIND_SELECTION = [
        ("exercise_image", "Exercise Image"),
        ("user_progress_photo", "User Progress Photo"),
        ("video", "Video"),
        ("document", "Document"),
    ]

    SOURCE_TYPE_SELECTION = [
        ("wger", "WGER"),
        ("upload", "Upload"),
        ("import", "Import"),
        ("camera", "Camera"),
    ]

    attachment_id = fields.Many2one(
        "ir.attachment",
        required=True,
        ondelete="cascade",
        auto_join=True,
        index=True,
    )
    name = fields.Char(related="attachment_id.name", readonly=False)
    datas = fields.Binary(related="attachment_id.datas", readonly=False)
    mimetype = fields.Char(related="attachment_id.mimetype", readonly=True)
    file_size = fields.Integer(related="attachment_id.file_size", readonly=True)
    checksum = fields.Char(related="attachment_id.checksum", readonly=True)
    media_kind = fields.Selection(
        selection=MEDIA_KIND_SELECTION,
        required=True,
        default="exercise_image",
        index=True,
    )
    exercise_id = fields.Many2one(
        "fitness.exercise",
        string="Exercise",
        ondelete="cascade",
        index=True,
    )
    owner_partner_id = fields.Many2one("res.partner", index=True)
    source_type = fields.Selection(selection=SOURCE_TYPE_SELECTION, index=True)
    source_url = fields.Char(index=True)
    external_uid = fields.Char(index=True)
    is_primary = fields.Boolean(default=False, index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    @api.constrains("is_primary", "exercise_id", "active")
    def _check_unique_primary(self):
        for rec in self.filtered(lambda x: x.is_primary and x.exercise_id and x.active):
            duplicate_count = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("exercise_id", "=", rec.exercise_id.id),
                    ("is_primary", "=", True),
                    ("active", "=", True),
                ]
            )
            if duplicate_count:
                raise ValidationError(
                    _("Only one primary media is allowed per exercise.")
                )

    @api.constrains("external_uid", "exercise_id")
    def _check_unique_external_uid(self):
        for rec in self.filtered(lambda x: x.external_uid and x.exercise_id):
            duplicate_count = self.search_count(
                [
                    ("id", "!=", rec.id),
                    ("exercise_id", "=", rec.exercise_id.id),
                    ("external_uid", "=", rec.external_uid),
                ]
            )
            if duplicate_count:
                raise ValidationError(
                    _("Media external UID must be unique for each exercise.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()
        for vals in vals_list:
            vals = vals.copy()
            if not vals.get("attachment_id"):
                attachment_name = vals.get("name") or "Media"
                attachment = self.env["ir.attachment"].create(
                    {
                        "name": attachment_name,
                        "datas": vals.get("datas"),
                        "res_model": "fitness.exercise"
                        if vals.get("exercise_id")
                        else False,
                        "res_id": vals.get("exercise_id") or 0,
                        "type": "binary",
                        "mimetype": vals.get("mimetype"),
                    }
                )
                vals["attachment_id"] = attachment.id
            rec = super().create([vals])
            rec.attachment_id.fitness_media_id = rec.id
            records |= rec
            rec._synchronize_primary_media()
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            rec.attachment_id.fitness_media_id = rec.id
            if rec.exercise_id:
                rec.attachment_id.write(
                    {
                        "res_model": "fitness.exercise",
                        "res_id": rec.exercise_id.id,
                    }
                )
        self._synchronize_primary_media()
        return result

    def unlink(self):
        attachments = self.mapped("attachment_id")
        result = super().unlink()
        attachments.unlink()
        return result

    def _synchronize_primary_media(self):
        for rec in self.filtered("exercise_id"):
            if rec.is_primary:
                others = self.search(
                    [
                        ("id", "!=", rec.id),
                        ("exercise_id", "=", rec.exercise_id.id),
                        ("is_primary", "=", True),
                    ]
                )
                if others:
                    others.write({"is_primary": False})
                rec.exercise_id.write(
                    {
                        "main_media_id": rec.id,
                        "image_1920": rec.attachment_id.datas,
                    }
                )
            elif not rec.exercise_id.main_media_id:
                rec.write({"is_primary": True})

    def action_set_primary(self):
        self.ensure_one()
        if self.exercise_id:
            old_primary = self.search(
                [
                    ("id", "!=", self.id),
                    ("exercise_id", "=", self.exercise_id.id),
                    ("is_primary", "=", True),
                ]
            )
            if old_primary:
                old_primary.write({"is_primary": False})
        self.write({"is_primary": True})
        return True

    @api.model
    def create_or_update_from_exercise_url(
        self,
        exercise,
        source_url,
        source_type="wger",
        media_kind="exercise_image",
        external_uid=False,
        set_primary=True,
    ):
        self = self.sudo()
        domain = [("exercise_id", "=", exercise.id), ("source_url", "=", source_url)]
        if external_uid:
            domain = [
                "|",
                ("external_uid", "=", external_uid),
                "&",
                ("exercise_id", "=", exercise.id),
                ("source_url", "=", source_url),
            ]
        existing = self.search(domain, limit=1)
        if existing:
            if set_primary:
                existing.action_set_primary()
            return existing

        image_bytes = exercise._fetch_binary(source_url)
        file_name = source_url.rsplit("/", 1)[-1] or f"exercise-{exercise.id}.img"
        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(image_bytes),
                "res_model": "fitness.exercise",
                "res_id": exercise.id,
                "type": "binary",
            }
        )
        media = self.create(
            {
                "attachment_id": attachment.id,
                "name": attachment.name,
                "media_kind": media_kind,
                "exercise_id": exercise.id,
                "source_type": source_type,
                "source_url": source_url,
                "external_uid": external_uid,
                "is_primary": set_primary,
                "company_id": exercise.company_id.id,
            }
        )
        return media
