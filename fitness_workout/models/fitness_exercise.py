import uuid

from odoo import api, fields, models


class FitnessExerciseCategory(models.Model):
    _name = "fitness.exercise.category"
    _description = "Exercise Category"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    exercise_ids = fields.One2many(
        "fitness.exercise", "category_id", string="Exercises"
    )
    exercise_count = fields.Integer(compute="_compute_exercise_count")

    @api.depends("exercise_ids")
    def _compute_exercise_count(self):
        for rec in self:
            rec.exercise_count = len(rec.exercise_ids)


class FitnessEquipment(models.Model):
    _name = "fitness.equipment"
    _description = "Equipment"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)


class FitnessMuscle(models.Model):
    _name = "fitness.muscle"
    _description = "Muscle"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        required=True,
        translate=True,
    )
    name_en = fields.Char(
        translate=True,
    )
    is_front = fields.Boolean(
        default=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)


class FitnessExercise(models.Model):
    _name = "fitness.exercise"
    _description = "Exercise"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _order = "name"

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()),
        readonly=True,
        copy=False,
        index=True,
    )
    name = fields.Char(required=True, translate=True, index=True)
    description = fields.Text(translate=True)
    category_id = fields.Many2one(
        "fitness.exercise.category",
        string="Category",
        required=True,
        ondelete="restrict",
    )
    muscle_ids = fields.Many2many(
        "fitness.muscle",
        "fitness_exercise_muscle_rel",
        "exercise_id",
        "muscle_id",
        string="Primary Muscles",
    )
    muscles_secondary_ids = fields.Many2many(
        "fitness.muscle",
        "fitness_exercise_muscle_secondary_rel",
        "exercise_id",
        "muscle_id",
        string="Secondary Muscles",
    )
    equipment_ids = fields.Many2many(
        "fitness.equipment",
        "fitness_exercise_equipment_rel",
        "exercise_id",
        "equipment_id",
        string="Equipment",
    )
    variation_group = fields.Char(help="UUID grouping exercise variations")
    video_url = fields.Char(help="YouTube or other video URL")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_exercise_uuid_uniq", "unique(uuid)", "Exercise UUID must be unique."),
    ]

    @api.depends("name", "category_id")
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name]
            if rec.category_id:
                parts.append(f"[{rec.category_id.name}]")
            rec.display_name = " ".join(parts)
