from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessExercise(models.Model):
    _inherit = "fitness.exercise"

    media_ids = fields.One2many("fitness.media", "exercise_id", string="Exercise Media")
    main_media_id = fields.Many2one(
        "fitness.media",
        string="Main Media",
        domain="[('exercise_id', '=', id), ('media_kind', '=', 'exercise_image')]",
    )

    @api.onchange("main_media_id")
    def _onchange_main_media_id(self):
        for rec in self:
            if rec.main_media_id:
                rec.image_1920 = rec.main_media_id.attachment_id.datas


class FitnessMedia(models.Model):
    _inherit = "fitness.media"
    _order = "is_primary desc, id desc"

    exercise_id = fields.Many2one(
        "fitness.exercise",
        string="Exercise",
        ondelete="cascade",
        index=True,
    )
    is_primary = fields.Boolean(default=False, index=True)
    wger_image_id = fields.Integer(index=True)
    wger_image_uuid = fields.Char(index=True)
    wger_style = fields.Char()

    @api.constrains("is_primary", "exercise_id", "active")
    def _check_unique_primary(self):
        for rec in self.filtered(lambda r: r.is_primary and r.exercise_id and r.active):
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
        for rec in self.filtered(lambda r: r.external_uid and r.exercise_id):
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
        records = super().create(vals_list)
        for rec in records:
            if rec.exercise_id:
                rec.attachment_id.write(
                    {
                        "res_model": "fitness.exercise",
                        "res_id": rec.exercise_id.id,
                    }
                )
        records._synchronize_primary_media()
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            if rec.exercise_id:
                rec.attachment_id.write(
                    {
                        "res_model": "fitness.exercise",
                        "res_id": rec.exercise_id.id,
                    }
                )
        self._synchronize_primary_media()
        return result

    def _synchronize_primary_media(self):
        for rec in self.filtered("exercise_id"):
            if rec.is_primary:
                others = self.search(
                    [
                        ("id", "!=", rec.id),
                        ("exercise_id", "=", rec.exercise_id.id),
                        ("is_primary", "=", True),
                        ("active", "=", True),
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
            elif rec.exercise_id.main_media_id == rec:
                fallback = self.search(
                    [
                        ("exercise_id", "=", rec.exercise_id.id),
                        ("active", "=", True),
                        ("id", "!=", rec.id),
                    ],
                    order="id",
                    limit=1,
                )
                if fallback:
                    fallback.write({"is_primary": True})
                else:
                    rec.exercise_id.write({"main_media_id": False, "image_1920": False})

    def action_set_primary(self):
        self.ensure_one()
        if self.exercise_id:
            old_primary = self.search(
                [
                    ("id", "!=", self.id),
                    ("exercise_id", "=", self.exercise_id.id),
                    ("is_primary", "=", True),
                    ("active", "=", True),
                ]
            )
            if old_primary:
                old_primary.write({"is_primary": False})
        self.write({"is_primary": True})
        return True
