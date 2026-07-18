import uuid
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessPlanV2(models.Model):
    _name = "fitness.plan.v2"
    _description = "Workout Plan Project V2"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start desc, create_date desc"

    PLAN_SCOPE_SELECTION = [
        ("template", "Template"),
        ("user", "User Workout"),
    ]

    STATE_SELECTION = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("done", "Done"),
        ("archived", "Archived"),
    ]

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()), readonly=True, copy=False, index=True
    )
    name = fields.Char(required=True, translate=True, tracking=True)
    description = fields.Text(translate=True)
    plan_scope = fields.Selection(
        selection=PLAN_SCOPE_SELECTION, default="template", required=True, tracking=True
    )
    partner_id = fields.Many2one("res.partner", tracking=True)
    start = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    end = fields.Date(required=True, tracking=True)
    is_template = fields.Boolean(default=True, tracking=True)
    is_public = fields.Boolean(default=True, tracking=True)
    state = fields.Selection(
        selection=STATE_SELECTION, default="draft", required=True, tracking=True
    )
    phase_ids = fields.One2many("fitness.plan.v2.phase", "plan_id", string="Phases")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_plan_v2_uuid_uniq", "unique(uuid)", "Plan V2 UUID must be unique."),
    ]

    @api.constrains("start", "end")
    def _check_dates(self):
        for rec in self:
            if rec.start and rec.end and rec.end < rec.start:
                raise ValidationError(
                    _("End date must be greater than or equal to start date.")
                )

    @api.constrains("plan_scope", "partner_id")
    def _check_partner_for_user_scope(self):
        for rec in self:
            if rec.plan_scope == "user" and not rec.partner_id:
                raise ValidationError(_("Partner is required for user workouts."))

    def unlink(self):
        for plan in self:
            activities = self.env["fitness.plan.v2.activity"].search(
                [("day_id.phase_id.plan_id", "=", plan.id)]
            )
            lines = self.env["fitness.plan.v2.line"].search(
                [("block_id.day_id.phase_id.plan_id", "=", plan.id)]
            )
            blocks = self.env["fitness.plan.v2.block"].search(
                [("day_id.phase_id.plan_id", "=", plan.id)]
            )
            days = self.env["fitness.plan.v2.day"].search(
                [("phase_id.plan_id", "=", plan.id)]
            )
            phases = self.env["fitness.plan.v2.phase"].search(
                [("plan_id", "=", plan.id)]
            )
            activities.unlink()
            lines.unlink()
            blocks.unlink()
            days.unlink()
            phases.unlink()
        return super().unlink()

    @api.onchange("plan_scope")
    def _onchange_plan_scope(self):
        for rec in self:
            rec.is_template = rec.plan_scope == "template"


class FitnessPlanV2Phase(models.Model):
    _name = "fitness.plan.v2.phase"
    _description = "Workout Plan Project V2 Phase"
    _order = "sequence, id"

    plan_id = fields.Many2one(
        "fitness.plan.v2", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(related="plan_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="plan_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="plan_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    start_offset = fields.Integer(default=1, required=True)
    end_offset = fields.Integer(default=2, required=True)
    day_ids = fields.One2many("fitness.plan.v2.day", "phase_id", string="Days")
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)


class FitnessPlanV2Day(models.Model):
    _name = "fitness.plan.v2.day"
    _description = "Workout Plan Project V2 Day"
    _order = "sequence, id"

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

    phase_id = fields.Many2one(
        "fitness.plan.v2.phase", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="phase_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="phase_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="phase_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="phase_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True, translate=True)
    day_type = fields.Selection(
        selection=DAY_TYPE_SELECTION, default="custom", required=True
    )
    is_rest = fields.Boolean(default=False)
    notes = fields.Char()
    block_ids = fields.One2many("fitness.plan.v2.block", "day_id", string="Blocks")
    activity_ids = fields.One2many(
        "fitness.plan.v2.activity", "day_id", string="Activities"
    )
    company_id = fields.Many2one(related="phase_id.company_id", store=True, index=True)


class FitnessPlanV2Block(models.Model):
    _name = "fitness.plan.v2.block"
    _description = "Workout Plan Project V2 Block"
    _order = "sequence, id"

    BLOCK_TYPE_SELECTION = [
        ("single", "Single"),
        ("superset", "Superset"),
        ("circuit", "Circuit"),
        ("amrap", "AMRAP"),
        ("emom", "EMOM"),
    ]

    day_id = fields.Many2one(
        "fitness.plan.v2.day", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="day_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="day_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="day_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="day_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True)
    block_type = fields.Selection(
        selection=BLOCK_TYPE_SELECTION, default="single", required=True
    )
    notes = fields.Char()
    line_ids = fields.One2many(
        "fitness.plan.v2.line", "block_id", string="Exercise Lines"
    )
    company_id = fields.Many2one(related="day_id.company_id", store=True, index=True)


class FitnessPlanV2Activity(models.Model):
    _name = "fitness.plan.v2.activity"
    _description = "Workout Plan V2 Activity Card"
    _order = "sequence, id"

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

    day_id = fields.Many2one(
        "fitness.plan.v2.day", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="day_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="day_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="day_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="day_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    exercise_id = fields.Many2one(
        "fitness.exercise", required=True, ondelete="restrict"
    )
    exercise_type = fields.Selection(
        selection=EXERCISE_TYPE_SELECTION, default="normal", required=True
    )
    sets = fields.Integer(default=3)
    reps = fields.Float(digits=(6, 2))
    repetition_unit_id = fields.Many2one("fitness.repetition.unit")
    weight = fields.Float(digits=(8, 2))
    weight_unit_id = fields.Many2one("fitness.weight.unit")
    rir = fields.Float(digits=(4, 1))
    rest_seconds = fields.Integer()
    notes = fields.Char()
    scheduled_date = fields.Date(index=True)
    company_id = fields.Many2one(related="day_id.company_id", store=True, index=True)

    @api.onchange("day_id")
    def _onchange_day_id_compute_date(self):
        for rec in self:
            if rec.day_id and not rec.scheduled_date:
                rec.scheduled_date = rec._compute_scheduled_date_from_plan()

    def _compute_scheduled_date_from_plan(self):
        self.ensure_one()
        if (
            self.day_id
            and self.day_id.plan_id
            and self.day_id.plan_id.start
            and self.day_id.phase_id
        ):
            return self.day_id.plan_id.start + timedelta(
                weeks=(self.day_id.phase_id.start_offset - 1),
                days=(self.day_id.sequence - 1),
            )
        return False

    def action_open_plan(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "fitness.plan.v2",
            "res_id": self.plan_id.id,
            "view_mode": "form",
            "target": "current",
        }


class FitnessPlanV2Line(models.Model):
    _name = "fitness.plan.v2.line"
    _description = "Workout Plan Project V2 Exercise Line"
    _order = "sequence, id"

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

    block_id = fields.Many2one(
        "fitness.plan.v2.block", required=True, ondelete="cascade", index=True
    )
    day_id = fields.Many2one(related="block_id.day_id", store=True, index=True)
    plan_id = fields.Many2one(related="block_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="block_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="block_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="block_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    exercise_id = fields.Many2one(
        "fitness.exercise", required=True, ondelete="restrict"
    )
    exercise_type = fields.Selection(
        selection=EXERCISE_TYPE_SELECTION, default="normal", required=True
    )
    sets = fields.Integer(default=3)
    reps = fields.Float(digits=(6, 2))
    repetition_unit_id = fields.Many2one("fitness.repetition.unit")
    weight = fields.Float(digits=(8, 2))
    weight_unit_id = fields.Many2one("fitness.weight.unit")
    rir = fields.Float(digits=(4, 1))
    rest_seconds = fields.Integer()
    notes = fields.Char()
    company_id = fields.Many2one(related="block_id.company_id", store=True, index=True)
