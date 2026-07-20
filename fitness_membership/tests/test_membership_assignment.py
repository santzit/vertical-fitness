# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestMembershipAssignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.template = cls.env["fitness.workout.plan"].create(
            {
                "name": "Template Assignment Test",
                "plan_scope": "template",
                "start": today,
                "end": today + timedelta(days=6),
                "is_template": True,
                "is_public": True,
            }
        )
        cls.allowed_member = cls.env["res.partner"].create(
            {"name": "Allowed Member", "free_member": True}
        )
        cls.blocked_member = cls.env["res.partner"].create({"name": "Blocked Member"})

    def test_assign_selected_rejects_non_partner_active_context(self):
        with self.assertRaises(UserError):
            self.template.with_context(
                active_model="fitness.workout.plan",
                active_id=self.template.id,
            ).action_assign_selected_to_member()

    def test_assign_templates_rejects_non_active_member(self):
        with self.assertRaises(UserError):
            self.template.with_context(
                target_partner_id=self.blocked_member.id,
            ).action_assign_templates_to_member()

    def test_assign_selected_allows_free_member(self):
        plans = self.env["fitness.workout.plan"].search_count(
            [
                ("plan_scope", "=", "user"),
                ("partner_id", "=", self.allowed_member.id),
                ("origin_template_id", "=", self.template.id),
            ]
        )
        action = self.template.with_context(
            target_partner_id=self.allowed_member.id,
            active_model="res.partner",
            active_id=self.allowed_member.id,
        ).action_assign_selected_to_member()
        new_plans = self.env["fitness.workout.plan"].search_count(
            [
                ("plan_scope", "=", "user"),
                ("partner_id", "=", self.allowed_member.id),
                ("origin_template_id", "=", self.template.id),
            ]
        )
        self.assertEqual(action["res_model"], "fitness.workout.plan")
        self.assertEqual(new_plans, plans + 1)

    def test_assign_selected_prefers_target_partner_over_active_id(self):
        plans = self.env["fitness.workout.plan"].search_count(
            [
                ("plan_scope", "=", "user"),
                ("partner_id", "=", self.allowed_member.id),
                ("origin_template_id", "=", self.template.id),
            ]
        )
        self.template.with_context(
            target_partner_id=self.allowed_member.id,
            active_model="res.partner",
            active_id=self.blocked_member.id,
        ).action_assign_selected_to_member()
        new_plans = self.env["fitness.workout.plan"].search_count(
            [
                ("plan_scope", "=", "user"),
                ("partner_id", "=", self.allowed_member.id),
                ("origin_template_id", "=", self.template.id),
            ]
        )
        self.assertEqual(new_plans, plans + 1)
