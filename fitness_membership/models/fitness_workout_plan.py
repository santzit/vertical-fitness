from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class FitnessWorkoutPlan(models.Model):
    _inherit = "fitness.workout.plan"

    ASSIGNABLE_MEMBER_STATES = {"invoiced", "paid", "free"}

    origin_template_id = fields.Many2one(
        "fitness.workout.plan",
        string="Origin Template",
        readonly=True,
        ondelete="set null",
        help="Template this plan was assigned from",
    )

    def _get_target_partner(self):
        partner_id = self.env.context.get("target_partner_id") or self.env.context.get(
            "default_target_partner_id"
        )
        if not partner_id and self.env.context.get("active_model") == "res.partner":
            partner_id = self.env.context.get("active_id")
        if not partner_id:
            return self.env["res.partner"]
        return self.env["res.partner"].browse(partner_id).exists()

    def _ensure_assignable_member(self, partner):
        if not partner:
            raise UserError(
                _("No member selected. Please go back and select a member first.")
            )
        partner.ensure_one()
        if partner.membership_state not in self.ASSIGNABLE_MEMBER_STATES:
            raise UserError(
                _(
                    "Workout plans can only be assigned to members with an active "
                    "membership state (Invoiced, Paid, or Free)."
                )
            )
        return partner

    def action_assign_templates_to_member(self):
        target_partner = self._ensure_assignable_member(self._get_target_partner())
        template_list_view = self.env.ref(
            "fitness_membership.view_fitness_membership_template_list"
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign Workout Plans"),
            "res_model": "fitness.workout.plan",
            "view_mode": "list",
            "view_id": template_list_view.id,
            "domain": [("plan_scope", "=", "template")],
            "context": {
                "target_partner_id": target_partner.id,
                "default_target_partner_id": target_partner.id,
                "create": False,
            },
            "target": "current",
        }

    def action_assign_selected_to_member(self):
        target_partner = self._ensure_assignable_member(self._get_target_partner())
        templates = self.filtered(lambda t: t.plan_scope == "template")
        if not templates:
            raise UserError(_("Please select at least one workout template to assign."))

        assignment_date = fields.Date.context_today(self)
        new_plans = self.env["fitness.workout.plan"]

        for template in templates:
            new_plan = self._clone_plan_for_member(
                template, target_partner, assignment_date
            )
            new_plans |= new_plan

        return {
            "type": "ir.actions.act_window",
            "name": f"Workout Plans - {target_partner.name}",
            "res_model": "fitness.workout.plan",
            "view_mode": "list,form",
            "domain": [
                ("plan_scope", "=", "user"),
                ("partner_id", "=", target_partner.id),
            ],
            "context": {"create": False},
            "target": "current",
        }

    def _clone_plan_for_member(self, template, partner, assignment_date):
        template.ensure_one()
        template_duration = (template.end - template.start).days
        new_start = assignment_date
        new_end = assignment_date + timedelta(days=template_duration)

        new_plan = self.env["fitness.workout.plan"].create(
            {
                "name": template.name,
                "description": template.description,
                "plan_scope": "user",
                "partner_id": partner.id,
                "origin_template_id": template.id,
                "start": new_start,
                "end": new_end,
                "is_template": False,
                "is_public": False,
                "state": "draft",
            }
        )

        for day in template.day_ids.sorted("sequence"):
            new_day = self.env["fitness.workout.day"].create(
                {
                    "plan_id": new_plan.id,
                    "sequence": day.sequence,
                    "name": day.name,
                    "description": day.description,
                    "start_offset": day.start_offset,
                    "end_offset": day.end_offset,
                }
            )

            for slot in day.slot_ids.sorted("sequence"):
                new_slot = self.env["fitness.workout.slot"].create(
                    {
                        "day_id": new_day.id,
                        "sequence": slot.sequence,
                        "name": slot.name,
                        "slot_type": slot.slot_type,
                        "is_rest": slot.is_rest,
                        "notes": slot.notes,
                    }
                )

                for block in slot.block_ids.sorted("sequence"):
                    new_block = self.env["fitness.workout.block"].create(
                        {
                            "slot_id": new_slot.id,
                            "sequence": block.sequence,
                            "name": block.name,
                            "block_type": block.block_type,
                            "notes": block.notes,
                        }
                    )

                    for entry in block.entry_ids.sorted("sequence"):
                        self.env["fitness.workout.entry"].create(
                            {
                                "block_id": new_block.id,
                                "sequence": entry.sequence,
                                "exercise_id": entry.exercise_id.id,
                                "exercise_type": entry.exercise_type,
                                "sets": entry.sets,
                                "reps": entry.reps,
                                "repetition_unit_id": entry.repetition_unit_id.id,
                                "weight": entry.weight,
                                "weight_unit_id": entry.weight_unit_id.id,
                                "rir": entry.rir,
                                "rest_seconds": entry.rest_seconds,
                            }
                        )

                for card in slot.card_ids.sorted("sequence"):
                    scheduled_date = self._compute_new_scheduled_date(
                        new_plan, day, slot
                    )
                    self.env["fitness.workout.card"].create(
                        {
                            "slot_id": new_slot.id,
                            "sequence": card.sequence,
                            "exercise_id": card.exercise_id.id,
                            "exercise_type": card.exercise_type,
                            "sets": card.sets,
                            "reps": card.reps,
                            "repetition_unit_id": card.repetition_unit_id.id,
                            "weight": card.weight,
                            "weight_unit_id": card.weight_unit_id.id,
                            "rir": card.rir,
                            "rest_seconds": card.rest_seconds,
                            "notes": card.notes,
                            "scheduled_date": scheduled_date,
                        }
                    )

        return new_plan

    def _compute_new_scheduled_date(self, plan, day, slot):
        if plan.start and day.start_offset:
            return plan.start + timedelta(
                weeks=(day.start_offset - 1),
                days=(slot.sequence - 1),
            )
        return False
