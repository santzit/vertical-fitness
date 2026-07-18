from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    fitness_media_id = fields.Many2one("fitness.media", index=True)


class FitnessExercise(models.Model):
    _inherit = "fitness.exercise"

    media_ids = fields.One2many("fitness.media", "exercise_id", string="Exercise Media")
    main_media_id = fields.Many2one(
        "fitness.media",
        string="Main Media",
        domain="[('exercise_id', '=', id), ('media_kind', '=', 'exercise_image')]",
    )

    def _sync_single_wger_image(self):
        self.ensure_one()
        values = {
            "wger_image_synced_at": fields.Datetime.now(),
        }
        try:
            image_url = self._get_wger_image_url(self.wger_id)
            values["wger_image_url"] = image_url or False
        except Exception as exc:
            values.update(
                {
                    "wger_image_sync_status": "error",
                    "wger_image_sync_message": f"WGER request failed: {exc}",
                }
            )
            self.write(values)
            return

        if not image_url:
            values.update(
                {
                    "wger_image_sync_status": "missing",
                    "wger_image_sync_message": "No image returned by WGER.",
                }
            )
            self.write(values)
            return

        try:
            media = self.env["fitness.media"].create_or_update_from_exercise_url(
                exercise=self,
                source_url=image_url,
                source_type="wger",
                media_kind="exercise_image",
                external_uid=f"wger:{self.wger_id}:{image_url.rsplit('/', 1)[-1]}",
                set_primary=True,
            )
            values.update(
                {
                    "main_media_id": media.id,
                    "image_1920": media.attachment_id.datas,
                    "wger_image_sync_status": "ok",
                    "wger_image_sync_message": "Image synced from WGER.",
                }
            )
        except Exception as exc:
            values.update(
                {
                    "wger_image_sync_status": "error",
                    "wger_image_sync_message": str(exc),
                }
            )
        self.write(values)

    @api.onchange("main_media_id")
    def _onchange_main_media_id(self):
        for rec in self:
            if rec.main_media_id:
                rec.image_1920 = rec.main_media_id.attachment_id.datas
