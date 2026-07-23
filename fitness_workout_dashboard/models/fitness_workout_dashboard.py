from datetime import timedelta

from odoo import fields, models


class FitnessWorkoutDashboard(models.Model):
    _name = "fitness.workout.dashboard"
    _description = "Fitness Workout Dashboard"
    _rec_name = "company_id"

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    active_user_plans_count = fields.Integer(compute="_compute_kpis")
    draft_user_plans_count = fields.Integer(compute="_compute_kpis")
    due_today_cards_count = fields.Integer(compute="_compute_kpis")
    overdue_cards_count = fields.Integer(compute="_compute_kpis")
    due_next_7_days_count = fields.Integer(compute="_compute_kpis")

    _sql_constraints = [
        (
            "fitness_workout_dashboard_company_uniq",
            "unique(company_id)",
            "A dashboard already exists for this company.",
        )
    ]

    def _user_plan_domain(self):
        self.ensure_one()
        return [("company_id", "=", self.company_id.id), ("plan_scope", "=", "user")]

    def _card_domain(self):
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("plan_scope", "=", "user"),
            ("plan_id.active", "=", True),
        ]

    def _compute_kpis(self):
        plan_model = self.env["fitness.workout.plan"].sudo()
        card_model = self.env["fitness.workout.card"].sudo()
        today = fields.Date.context_today(self)
        for rec in self:
            plan_domain = rec._user_plan_domain()
            rec.active_user_plans_count = plan_model.search_count(
                plan_domain + [("state", "=", "active"), ("active", "=", True)]
            )
            rec.draft_user_plans_count = plan_model.search_count(
                plan_domain + [("state", "=", "draft"), ("active", "=", True)]
            )

            card_domain = rec._card_domain()
            rec.due_today_cards_count = card_model.search_count(
                card_domain + [("scheduled_date", "=", today)]
            )
            rec.overdue_cards_count = card_model.search_count(
                card_domain + [("scheduled_date", "<", today)]
            )
            rec.due_next_7_days_count = card_model.search_count(
                card_domain
                + [
                    ("scheduled_date", ">", today),
                    ("scheduled_date", "<=", today + timedelta(days=7)),
                ]
            )

    def action_view_active_plans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Active User Plans",
            "res_model": "fitness.workout.plan",
            "view_mode": "kanban,list,form,calendar",
            "domain": self._user_plan_domain()
            + [("state", "=", "active"), ("active", "=", True)],
        }

    def action_view_draft_plans(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Draft User Plans",
            "res_model": "fitness.workout.plan",
            "view_mode": "kanban,list,form,calendar",
            "domain": self._user_plan_domain()
            + [("state", "=", "draft"), ("active", "=", True)],
        }

    def action_view_cards(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return {
            "type": "ir.actions.act_window",
            "name": "Workout Cards",
            "res_model": "fitness.workout.card",
            "view_mode": "kanban,list,form",
            "domain": self._card_domain()
            + [
                ("scheduled_date", "!=", False),
                ("scheduled_date", "<=", today + timedelta(days=7)),
            ],
        }
