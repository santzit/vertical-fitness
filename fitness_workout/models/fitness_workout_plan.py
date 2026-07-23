import uuid
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FitnessWorkoutPlan(models.Model):
    _name = "fitness.workout.plan"
    _description = "Workout Plan"
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
    duration = fields.Integer(
        compute="_compute_duration", store=True, string="Duration (Days)"
    )
    duration_text = fields.Char(
        compute="_compute_duration", store=True, string="Duration"
    )
    day_ids = fields.One2many("fitness.workout.day", "plan_id", string="Days")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_workout_plan_uuid_uniq", "unique(uuid)", "Plan UUID must be unique."),
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

    @api.depends("start", "end")
    def _compute_duration(self):
        for rec in self:
            if rec.start and rec.end:
                total_days = (rec.end - rec.start).days
                weeks = total_days // 7
                days = total_days % 7
                rec.duration = total_days
                if weeks and days:
                    rec.duration_text = _("%(weeks)d weeks, %(days)d days") % {
                        "weeks": weeks,
                        "days": days,
                    }
                elif weeks:
                    rec.duration_text = _("%(weeks)d weeks") % {"weeks": weeks}
                else:
                    rec.duration_text = _("%(days)d days") % {"days": days}
            else:
                rec.duration = 0
                rec.duration_text = ""

    def unlink(self):
        return super().unlink()

    def action_view_board(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "fitness_workout.action_fitness_workout_slot_board_from_plan"
        )
        duration = self.duration_text or ""
        action["name"] = f"{self.name} | {self.start} - {self.end} ({duration})"
        action["domain"] = [("plan_id", "=", self.id)]
        action["context"] = {
            "active_model": "fitness.workout.plan",
            "active_id": self.id,
            "default_plan_id": self.id,
        }
        return action

    @api.onchange("plan_scope")
    def _onchange_plan_scope(self):
        for rec in self:
            rec.is_template = rec.plan_scope == "template"


class FitnessWorkoutDay(models.Model):
    _name = "fitness.workout.day"
    _description = "Workout Day"
    _order = "sequence, id"

    plan_id = fields.Many2one(
        "fitness.workout.plan", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(related="plan_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="plan_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="plan_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    start_offset = fields.Integer(default=1, required=True)
    end_offset = fields.Integer(default=2, required=True)
    slot_ids = fields.One2many("fitness.workout.slot", "day_id", string="Slots")
    company_id = fields.Many2one(related="plan_id.company_id", store=True, index=True)


class FitnessWorkoutSlot(models.Model):
    _name = "fitness.workout.slot"
    _description = "Workout Slot"
    _order = "sequence, id"

    SLOT_TYPE_SELECTION = [
        ("custom", "Custom"),
        ("enom", "EMOM"),
        ("amrap", "AMRAP"),
        ("hiit", "HIIT"),
        ("tabata", "Tabata"),
        ("edt", "EDT"),
        ("rft", "RFT"),
        ("afap", "AFAP"),
    ]

    day_id = fields.Many2one(
        "fitness.workout.day", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="day_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="day_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="day_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="day_id.is_public", store=True)
    day_sequence = fields.Integer(related="day_id.sequence", store=True, string="Day Seq.")
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True, translate=True)
    slot_type = fields.Selection(
        selection=SLOT_TYPE_SELECTION, default="custom", required=True
    )
    is_rest = fields.Boolean(default=False)
    notes = fields.Char()
    block_ids = fields.One2many("fitness.workout.block", "slot_id", string="Blocks")
    card_ids = fields.One2many("fitness.workout.card", "slot_id", string="Slot Cards")
    company_id = fields.Many2one(related="day_id.company_id", store=True, index=True)

    board_title = fields.Char(compute="_compute_board_display", store=True)
    board_prescription = fields.Char(compute="_compute_board_display", store=True)

    @api.depends(
        "name",
        "card_ids.exercise_id",
        "card_ids.exercise_type",
        "card_ids.sets",
        "card_ids.reps",
        "card_ids.repetition_unit_id",
        "card_ids.weight",
        "card_ids.weight_unit_id",
    )
    def _compute_board_display(self):
        for rec in self:
            first_card = rec.card_ids[:1] if rec.card_ids else False
            if first_card:
                exercise_name = first_card.exercise_id.name or ""
                if first_card.exercise_type != "normal":
                    rec.board_title = f"{rec.name} ({first_card.exercise_type})"
                else:
                    if exercise_name != rec.name:
                        rec.board_title = f"{exercise_name}, {rec.name}"
                    else:
                        rec.board_title = rec.name

                parts = []
                if first_card.sets:
                    parts.append(f"{first_card.sets} sets")
                if first_card.reps:
                    rep_str = f"{first_card.reps:g}"
                    if first_card.repetition_unit_id:
                        rep_str += f" x {first_card.repetition_unit_id.name}"
                    if first_card.weight:
                        weight_str = f"{first_card.weight:g}"
                        if first_card.weight_unit_id:
                            weight_str += first_card.weight_unit_id.name
                        rep_str += f" {weight_str}"
                    parts.append(rep_str)
                rec.board_prescription = ", ".join(parts) if parts else rec.name
            else:
                rec.board_title = rec.name
                rec.board_prescription = rec.name

    def action_view_cards(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "fitness_workout.action_fitness_workout_card_from_plan"
        )
        action["name"] = self.name
        action["domain"] = [("slot_id", "=", self.id)]
        action["context"] = {
            "default_slot_id": self.id,
            "default_plan_id": self.plan_id.id,
            "search_default_group_by_slot_id": 1,
        }
        return action


class FitnessWorkoutBlock(models.Model):
    _name = "fitness.workout.block"
    _description = "Workout Block"
    _order = "sequence, id"

    BLOCK_TYPE_SELECTION = [
        ("single", "Single"),
        ("superset", "Superset"),
        ("circuit", "Circuit"),
        ("amrap", "AMRAP"),
        ("emom", "EMOM"),
    ]

    slot_id = fields.Many2one(
        "fitness.workout.slot", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="slot_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="slot_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="slot_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="slot_id.is_public", store=True)
    sequence = fields.Integer(default=1, required=True, index=True)
    name = fields.Char(required=True)
    block_type = fields.Selection(
        selection=BLOCK_TYPE_SELECTION, default="single", required=True
    )
    notes = fields.Char()
    entry_ids = fields.One2many(
        "fitness.workout.entry", "block_id", string="Exercise Entries"
    )
    company_id = fields.Many2one(related="slot_id.company_id", store=True, index=True)


class FitnessWorkoutCard(models.Model):
    _name = "fitness.workout.card"
    _description = "Workout Card"
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

    slot_id = fields.Many2one(
        "fitness.workout.slot", required=True, ondelete="cascade", index=True
    )
    plan_id = fields.Many2one(related="slot_id.plan_id", store=True, index=True)
    partner_id = fields.Many2one(related="slot_id.partner_id", store=True, index=True)
    plan_scope = fields.Selection(related="slot_id.plan_scope", store=True, index=True)
    is_public = fields.Boolean(related="slot_id.is_public", store=True)
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
    company_id = fields.Many2one(related="slot_id.company_id", store=True, index=True)

    @api.onchange("slot_id")
    def _onchange_slot_id_compute_date(self):
        for rec in self:
            if rec.slot_id and not rec.scheduled_date:
                rec.scheduled_date = rec._compute_scheduled_date_from_plan()

    def _compute_scheduled_date_from_plan(self):
        self.ensure_one()
        if (
            self.slot_id
            and self.slot_id.plan_id
            and self.slot_id.plan_id.start
            and self.slot_id.day_id
        ):
            return self.slot_id.plan_id.start + timedelta(
                weeks=(self.slot_id.day_id.start_offset - 1),
                days=(self.slot_id.sequence - 1),
            )
        return False

    def action_open_plan(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "fitness.workout.plan",
            "res_id": self.plan_id.id,
            "view_mode": "form",
            "target": "current",
        }


class FitnessWorkoutEntry(models.Model):
    _name = "fitness.workout.entry"
    _description = "Workout Entry"
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
        "fitness.workout.block", required=True, ondelete="cascade", index=True
    )
    slot_id = fields.Many2one(related="block_id.slot_id", store=True, index=True)
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
