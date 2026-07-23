from datetime import timedelta

from odoo import fields, models


class FitnessMembershipDashboard(models.Model):
    _name = "fitness.membership.dashboard"
    _description = "Fitness Membership Dashboard"
    _rec_name = "company_id"

    ACTIVE_MEMBER_STATES = ("invoiced", "paid", "free")

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    active_members_count = fields.Integer(compute="_compute_kpis")
    overdue_members_count = fields.Integer(compute="_compute_kpis")
    expiring_in_7_days_count = fields.Integer(compute="_compute_kpis")
    expiring_in_30_days_count = fields.Integer(compute="_compute_kpis")
    next_expiring_member_ids = fields.Many2many(
        "res.partner",
        compute="_compute_kpis",
        string="Top 10 Next Expiring Members",
    )

    _sql_constraints = [
        (
            "fitness_membership_dashboard_company_uniq",
            "unique(company_id)",
            "A dashboard already exists for this company.",
        )
    ]

    def _member_company_domain(self):
        self.ensure_one()
        return [
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_id.id),
        ]

    def _overdue_invoice_domain(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return [
            ("company_id", "=", self.company_id.id),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "in", ("not_paid", "partial")),
            ("invoice_date_due", "<", today),
            ("invoice_line_ids.product_id.membership", "=", True),
        ]

    def _next_expiring_domain(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return [
            ("membership_state", "in", self.ACTIVE_MEMBER_STATES),
            ("membership_stop", ">=", today),
            ("membership_stop", "!=", False),
        ] + self._member_company_domain()

    def _compute_kpis(self):
        partner_model = self.env["res.partner"].sudo()
        move_model = self.env["account.move"].sudo()
        today = fields.Date.context_today(self)
        for rec in self:
            active_domain = [
                ("membership_state", "in", rec.ACTIVE_MEMBER_STATES),
            ] + rec._member_company_domain()
            rec.active_members_count = partner_model.search_count(active_domain)

            grouped = move_model.read_group(
                rec._overdue_invoice_domain(),
                ["partner_id"],
                ["partner_id"],
                lazy=False,
            )
            rec.overdue_members_count = len(
                [group for group in grouped if group.get("partner_id")]
            )

            week_domain = [
                ("membership_stop", ">=", today),
                ("membership_stop", "<=", today + timedelta(days=7)),
                ("membership_state", "in", rec.ACTIVE_MEMBER_STATES),
            ] + rec._member_company_domain()
            rec.expiring_in_7_days_count = partner_model.search_count(week_domain)

            month_domain = [
                ("membership_stop", ">=", today),
                ("membership_stop", "<=", today + timedelta(days=30)),
                ("membership_state", "in", rec.ACTIVE_MEMBER_STATES),
            ] + rec._member_company_domain()
            rec.expiring_in_30_days_count = partner_model.search_count(month_domain)

            rec.next_expiring_member_ids = partner_model.search(
                rec._next_expiring_domain(),
                order="membership_stop asc, id asc",
                limit=10,
            )

    def action_view_active_members(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Active Members",
            "res_model": "res.partner",
            "view_mode": "list,form",
            "search_view_id": self.env.ref(
                "membership.view_res_partner_member_filter"
            ).id,
            "domain": [
                ("membership_state", "in", self.ACTIVE_MEMBER_STATES),
            ]
            + self._member_company_domain(),
            "context": {"search_default_all_members": 1},
        }

    def action_view_overdue_members(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return {
            "type": "ir.actions.act_window",
            "name": "Overdue Members",
            "res_model": "res.partner",
            "view_mode": "list,form",
            "search_view_id": self.env.ref(
                "membership.view_res_partner_member_filter"
            ).id,
            "domain": [
                (
                    "member_lines.account_invoice_id.invoice_line_ids.product_id.membership",
                    "=",
                    True,
                ),
                ("member_lines.account_invoice_id.move_type", "=", "out_invoice"),
                ("member_lines.account_invoice_id.state", "=", "posted"),
                (
                    "member_lines.account_invoice_id.payment_state",
                    "in",
                    ("not_paid", "partial"),
                ),
                ("member_lines.account_invoice_id.invoice_date_due", "<", today),
            ]
            + self._member_company_domain(),
            "context": {"search_default_all_members": 1},
        }

    def action_view_expiring_members(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Next Expiring Members",
            "res_model": "res.partner",
            "view_mode": "list,form",
            "search_view_id": self.env.ref(
                "membership.view_res_partner_member_filter"
            ).id,
            "domain": self._next_expiring_domain(),
            "context": {"search_default_all_members": 1},
            "limit": 10,
        }
