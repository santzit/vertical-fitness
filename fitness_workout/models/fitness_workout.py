import uuid

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessWorkoutSession(models.Model):
    _name = "fitness.workout.session"
    _description = "Workout Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    IMPRESSION_SELECTION = [
        ("bad", "Bad"),
        ("neutral", "Neutral"),
        ("good", "Good"),
    ]

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()), readonly=True, copy=False, index=True
    )
    partner_id = fields.Many2one("res.partner", required=True, tracking=True)
    plan_id = fields.Many2one("fitness.workout.plan", tracking=True)
    day_id = fields.Many2one(
        "fitness.workout.day", domain="[('plan_id', '=', plan_id)]"
    )
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    notes = fields.Text()
    impression = fields.Selection(
        selection=IMPRESSION_SELECTION, default="neutral", required=True
    )
    time_start = fields.Float(help="Start time in hours", digits=(16, 2))
    time_end = fields.Float(help="End time in hours", digits=(16, 2))
    log_ids = fields.One2many(
        "fitness.workout.log", "session_id", string="Workout Logs"
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    _sql_constraints = [
        (
            "fitness_workout_session_uuid_uniq",
            "unique(uuid)",
            "Session UUID must be unique.",
        ),
    ]


class FitnessWorkoutLog(models.Model):
    _name = "fitness.workout.log"
    _description = "Workout Log"
    _order = "date desc"

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()), readonly=True, copy=False, index=True
    )
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    next_log_id = fields.Many2one("fitness.workout.log", ondelete="set null")
    session_id = fields.Many2one("fitness.workout.session", ondelete="set null")
    exercise_id = fields.Many2one(
        "fitness.exercise", required=True, ondelete="restrict"
    )
    plan_id = fields.Many2one("fitness.workout.plan", ondelete="set null")
    entry_id = fields.Many2one("fitness.workout.entry", ondelete="set null")
    iteration = fields.Integer()
    repetitions_unit_id = fields.Many2one("fitness.repetition.unit")
    repetitions = fields.Float(digits=(16, 2))
    repetitions_target = fields.Float(digits=(16, 2))
    weight_unit_id = fields.Many2one("fitness.weight.unit")
    weight = fields.Float(digits=(16, 2))
    weight_target = fields.Float(digits=(16, 2))
    rir = fields.Float(digits=(3, 1))
    rir_target = fields.Float(digits=(3, 1))
    rest = fields.Integer()
    rest_target = fields.Integer()
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    _sql_constraints = [
        (
            "fitness_workout_log_uuid_uniq",
            "unique(uuid)",
            "Workout log UUID must be unique.",
        ),
    ]

    @api.constrains("repetitions", "weight", "repetitions_unit_id", "weight_unit_id")
    def _check_values(self):
        for rec in self:
            if not rec.repetitions and not rec.weight:
                raise ValidationError(_("At least repetitions or weight must be set."))
            if rec.repetitions and not rec.repetitions_unit_id:
                raise ValidationError(
                    _("Please set a repetitions unit when repetitions are entered.")
                )
            if rec.weight and not rec.weight_unit_id:
                raise ValidationError(
                    _("Please set a weight unit when weight is entered.")
                )
