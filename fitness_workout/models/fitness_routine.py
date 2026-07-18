import uuid

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessRoutine(models.Model):
    _name = "fitness.routine"
    _description = "Workout Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start desc, create_date desc"

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()), readonly=True, copy=False, index=True
    )
    name = fields.Char(required=True, translate=True, tracking=True)
    description = fields.Text(translate=True)
    partner_id = fields.Many2one("res.partner", required=True, tracking=True)
    start = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    end = fields.Date(required=True, tracking=True)
    is_template = fields.Boolean(default=False)
    is_public = fields.Boolean(default=False)
    fit_in_week = fields.Boolean(default=False)
    day_ids = fields.One2many("fitness.day", "routine_id", string="Days")
    label_ids = fields.One2many("fitness.label", "routine_id", string="Labels")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_routine_uuid_uniq", "unique(uuid)", "Routine UUID must be unique."),
    ]

    @api.constrains("start", "end")
    def _check_dates(self):
        for rec in self:
            if rec.start and rec.end and rec.end < rec.start:
                raise ValidationError(
                    _("End date must be greater than or equal to start date.")
                )


class FitnessDay(models.Model):
    _name = "fitness.day"
    _description = "Workout Plan Day"
    _order = "order, id"

    DAY_TYPE_SELECTION = [
        ("custom", "Custom"),
        ("enom", "EMOM"),
        ("amrap", "AMRAP"),
        ("hiit", "HIIT"),
        ("tabata", "Tabata"),
        ("edt", "EDT"),
        ("rft", "RFT"),
        ("afap", "AFAP"),
    ]

    routine_id = fields.Many2one("fitness.routine", required=True, ondelete="cascade")
    partner_id = fields.Many2one(
        related="routine_id.partner_id", store=True, index=True
    )
    is_template = fields.Boolean(related="routine_id.is_template", store=True)
    order = fields.Integer(default=1, required=True, index=True)
    day_type = fields.Selection(
        selection=DAY_TYPE_SELECTION, default="custom", required=True
    )
    name = fields.Char(translate=True)
    description = fields.Text(translate=True)
    is_rest = fields.Boolean(default=False)
    need_logs_to_advance = fields.Boolean(default=False)
    config = fields.Json()
    slot_ids = fields.One2many("fitness.slot", "day_id", string="Slots")
    company_id = fields.Many2one(
        related="routine_id.company_id", store=True, index=True
    )


class FitnessSlot(models.Model):
    _name = "fitness.slot"
    _description = "Workout Plan Slot"
    _order = "order, id"

    day_id = fields.Many2one("fitness.day", required=True, ondelete="cascade")
    routine_id = fields.Many2one(related="day_id.routine_id", store=True, index=True)
    partner_id = fields.Many2one(related="day_id.partner_id", store=True, index=True)
    is_template = fields.Boolean(related="day_id.is_template", store=True)
    order = fields.Integer(default=1, required=True, index=True)
    comment = fields.Char()
    config = fields.Json()
    entry_ids = fields.One2many("fitness.slot.entry", "slot_id", string="Entries")
    company_id = fields.Many2one(related="day_id.company_id", store=True, index=True)


class FitnessSlotEntry(models.Model):
    _name = "fitness.slot.entry"
    _description = "Workout Plan Slot Entry"
    _order = "order, id"

    EXERCISE_TYPE_SELECTION = [
        ("normal", "Normal"),
        ("warmup", "Warm-up"),
        ("dropset", "Dropset"),
        ("myo", "Myo-reps"),
        ("partial", "Partial"),
        ("forced", "Forced"),
        ("tut", "TUT"),
        ("iso", "Iso-hold"),
        ("jump", "Jump"),
    ]

    slot_id = fields.Many2one("fitness.slot", required=True, ondelete="cascade")
    routine_id = fields.Many2one(related="slot_id.routine_id", store=True, index=True)
    partner_id = fields.Many2one(related="slot_id.partner_id", store=True, index=True)
    is_template = fields.Boolean(related="slot_id.is_template", store=True)
    exercise_id = fields.Many2one(
        "fitness.exercise", required=True, ondelete="restrict"
    )
    repetition_unit_id = fields.Many2one("fitness.repetition.unit")
    repetition_rounding = fields.Float(digits=(6, 2))
    weight_unit_id = fields.Many2one("fitness.weight.unit")
    weight_rounding = fields.Float(digits=(6, 2))
    order = fields.Integer(default=1, index=True)
    comment = fields.Char()
    exercise_type = fields.Selection(
        selection=EXERCISE_TYPE_SELECTION, default="normal", required=True
    )
    class_name = fields.Char()
    config = fields.Json()
    company_id = fields.Many2one(related="slot_id.company_id", store=True, index=True)


class FitnessLabel(models.Model):
    _name = "fitness.label"
    _description = "Workout Plan Label"
    _order = "start_offset"

    routine_id = fields.Many2one("fitness.routine", required=True, ondelete="cascade")
    partner_id = fields.Many2one(
        related="routine_id.partner_id", store=True, index=True
    )
    is_template = fields.Boolean(related="routine_id.is_template", store=True)
    start_offset = fields.Integer(default=1, required=True)
    end_offset = fields.Integer(default=2, required=True)
    label_text = fields.Char(required=True, translate=True)
    comment = fields.Char()
    company_id = fields.Many2one(
        related="routine_id.company_id", store=True, index=True
    )
