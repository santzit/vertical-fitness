from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class FitnessWorkoutDashboard(models.AbstractModel):
    _name = "fitness.workout.dashboard"
    _description = "Fitness Workout Dashboard Service"

    def _check_dashboard_access(self):
        user = self.env.user
        if not (
            user.has_group("fitness_workout.group_workout_trainer")
            or user.has_group("fitness_workout.group_workout_manager")
        ):
            raise AccessError(_("You are not allowed to open this dashboard."))

    def _membership_invoice_domain(self):
        today = fields.Date.context_today(self)
        return [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("invoice_line_ids.product_id.membership", "=", True),
        ], today

    def _trend_month_labels(self, months=6):
        today = fields.Date.context_today(self)
        start = today.replace(day=1)
        labels = [start.strftime("%b %Y")]
        cursor = start
        while len(labels) < months:
            if cursor.month == 1:
                cursor = cursor.replace(year=cursor.year - 1, month=12)
            else:
                cursor = cursor.replace(month=cursor.month - 1)
            labels.append(cursor.strftime("%b %Y"))
        labels.reverse()
        return labels

    def _build_membership_trend(self):
        labels = self._trend_month_labels()
        member_line_model = self.env["membership.membership_line"].sudo()
        rows = member_line_model.read_group(
            [
                ("date_from", "!=", False),
                (
                    "date_from",
                    ">=",
                    fields.Date.context_today(self) - timedelta(days=186),
                ),
            ],
            ["id:count"],
            ["date_from:month"],
            lazy=False,
        )
        buckets = {}
        for row in rows:
            month_range = row.get("__range", {}).get("date_from:month", {})
            month_from = month_range.get("from")
            if not month_from:
                continue
            month_label = fields.Date.from_string(month_from).strftime("%b %Y")
            buckets[month_label] = row["id_count"]
        values = [int(buckets.get(label, 0)) for label in labels]
        max_value = max(values) if values else 0
        bars = []
        for label, value in zip(labels, values, strict=False):
            percent = int((value / max_value) * 100) if max_value else 0
            bars.append({"label": label, "value": value, "percent": percent})
        return bars

    @api.model
    def get_dashboard_data(self):
        self._check_dashboard_access()
        partner_model = self.env["res.partner"].sudo()
        plan_model = self.env["fitness.workout.plan"].sudo()
        card_model = self.env["fitness.workout.card"].sudo()
        move_model = self.env["account.move"].sudo()
        today = fields.Date.context_today(self)

        active_members = partner_model.search_count(
            [("membership_state", "in", ["paid", "invoiced", "free"])]
        )

        base_invoice_domain, _ = self._membership_invoice_domain()
        overdue_domain = base_invoice_domain + [
            ("invoice_date_due", "<", today),
            ("payment_state", "in", ["not_paid", "partial"]),
        ]
        overdue_partners = move_model.read_group(
            overdue_domain,
            ["partner_id"],
            ["partner_id"],
            lazy=False,
        )
        overdue_members = len(
            [row for row in overdue_partners if row.get("partner_id")]
        )

        pending_memberships = partner_model.search_count(
            [("membership_state", "=", "waiting")]
        )

        next_expiring = partner_model.search(
            [
                ("membership_state", "in", ["paid", "invoiced", "free"]),
                ("membership_stop", "!=", False),
                ("membership_stop", ">=", today),
            ],
            order="membership_stop asc, id asc",
            limit=10,
        )

        recent_moves = move_model.search(
            base_invoice_domain,
            order="invoice_date desc, id desc",
            limit=10,
        )

        trainer_rows = plan_model.read_group(
            [("plan_scope", "=", "user"), ("active", "=", True)],
            ["create_uid"],
            ["create_uid"],
            lazy=False,
        )
        trainer_rows = sorted(
            [row for row in trainer_rows if row.get("create_uid")],
            key=lambda row: row.get("create_uid_count", 0),
            reverse=True,
        )[:10]

        due_today_count = card_model.search_count(
            [("plan_scope", "=", "user"), ("scheduled_date", "=", today)]
        )
        overdue_cards_count = card_model.search_count(
            [("plan_scope", "=", "user"), ("scheduled_date", "<", today)]
        )

        return {
            "kpis": {
                "active_members": active_members,
                "overdue_members": overdue_members,
                "pending_memberships": pending_memberships,
                "due_today_cards": due_today_count,
                "overdue_cards": overdue_cards_count,
            },
            "trend": self._build_membership_trend(),
            "next_expiring_members": [
                {
                    "name": member.name,
                    "membership_stop": member.membership_stop.isoformat()
                    if member.membership_stop
                    else "",
                    "membership_state": member.membership_state,
                }
                for member in next_expiring
            ],
            "recent_membership_invoices": [
                {
                    "name": move.name or move.ref or "Draft",
                    "partner": move.partner_id.name,
                    "due_date": move.invoice_date_due.isoformat()
                    if move.invoice_date_due
                    else "",
                    "payment_state": move.payment_state,
                }
                for move in recent_moves
            ],
            "trainer_ranking": [
                {
                    "name": row["create_uid"][1],
                    "plans_count": row.get("create_uid_count", 0),
                }
                for row in trainer_rows
            ],
        }
