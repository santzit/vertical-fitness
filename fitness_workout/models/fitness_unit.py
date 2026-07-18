from odoo import fields, models


class FitnessRepetitionUnit(models.Model):
    _name = "fitness.repetition.unit"
    _description = "Repetition Unit"
    _order = "unit_type, name"

    name = fields.Char(required=True, translate=True)
    unit_type = fields.Selection(
        selection=[
            ("repetitions", "Repetitions"),
            ("time", "Time"),
            ("distance", "Distance"),
        ],
        required=True,
        default="repetitions",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    def _is_repetitions(self):
        self.ensure_one()
        return self.unit_type == "repetitions"

    def _is_time(self):
        self.ensure_one()
        return self.unit_type == "time"

    def _is_distance(self):
        self.ensure_one()
        return self.unit_type == "distance"


class FitnessWeightUnit(models.Model):
    _name = "fitness.weight.unit"
    _description = "Weight Unit"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
