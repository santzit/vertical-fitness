from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    fitness_media_id = fields.Many2one("fitness.media", index=True)
