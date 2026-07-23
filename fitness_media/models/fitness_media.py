from odoo import api, fields, models


class FitnessMedia(models.Model):
    _name = "fitness.media"
    _description = "Fitness Media"
    _order = "id desc"

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
    owner_partner_id = fields.Many2one("res.partner", index=True)
    source_type = fields.Selection(selection=SOURCE_TYPE_SELECTION, index=True)
    source_url = fields.Char(index=True)
    external_uid = fields.Char(index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

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
                        "res_model": False,
                        "res_id": 0,
                        "type": "binary",
                        "mimetype": vals.get("mimetype"),
                    }
                )
                vals["attachment_id"] = attachment.id
            rec = super().create([vals])
            rec.attachment_id.fitness_media_id = rec.id
            records |= rec
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            rec.attachment_id.fitness_media_id = rec.id
        return result

    def unlink(self):
        attachments = self.mapped("attachment_id")
        result = super().unlink()
        attachments.unlink()
        return result
