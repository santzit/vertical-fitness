from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class FitnessPlanV2(models.Model):
    _inherit = "fitness.plan.v2"

    origin_template_id = fields.Many2one(
        "fitness.plan.v2",
        string="Origin Template",
        readonly=True,
        ondelete="set null",
        help="Template this plan was assigned from",
    )

    def action_assign_templates_to_member(self):
        target_partner_id = self.env.context.get("target_partner_id")
        if not target_partner_id:
            target_partner_id = self.env.context.get("active_id")
        template_list_view = self.env.ref(
            "fitness_membership.view_fitness_membership_template_list"
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign Workout Plans"),
            "res_model": "fitness.plan.v2",
            "view_mode": "list",
            "view_id": template_list_view.id,
            "domain": [("plan_scope", "=", "template")],
            "context": {
                "default_target_partner_id": target_partner_id,
                "create": False,
            },
            "target": "current",
        }

    def action_assign_selected_to_member(self):
        target_partner_id = self.env.context.get("target_partner_id")
        if not target_partner_id:
            raise UserError(
                _("No member selected. Please go back and select a member first.")
            )

        target_partner = self.env["res.partner"].browse(target_partner_id)
        templates = self.filtered(lambda t: t.plan_scope == "template")
        if not templates:
            raise UserError(_("Please select at least one workout template to assign."))

        assignment_date = fields.Date.context_today(self)
        new_plans = self.env["fitness.plan.v2"]

        for template in templates:
            new_plan = self._clone_plan_for_member(
                template, target_partner, assignment_date
            )
            new_plans |= new_plan

        return {
            "type": "ir.actions.act_window",
            "name": f"Workout Plans - {target_partner.name}",
            "res_model": "fitness.plan.v2",
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

        new_plan = self.env["fitness.plan.v2"].create(
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

        for phase in template.phase_ids.sorted("sequence"):
            new_phase = self.env["fitness.plan.v2.phase"].create(
                {
                    "plan_id": new_plan.id,
                    "sequence": phase.sequence,
                    "name": phase.name,
                    "description": phase.description,
                    "start_offset": phase.start_offset,
                    "end_offset": phase.end_offset,
                }
            )

            for day in phase.day_ids.sorted("sequence"):
                new_day = self.env["fitness.plan.v2.day"].create(
                    {
                        "phase_id": new_phase.id,
                        "sequence": day.sequence,
                        "name": day.name,
                        "day_type": day.day_type,
                        "is_rest": day.is_rest,
                        "notes": day.notes,
                    }
                )

                for block in day.block_ids.sorted("sequence"):
                    new_block = self.env["fitness.plan.v2.block"].create(
                        {
                            "day_id": new_day.id,
                            "sequence": block.sequence,
                            "name": block.name,
                            "block_type": block.block_type,
                            "notes": block.notes,
                        }
                    )

                    for line in block.line_ids.sorted("sequence"):
                        self.env["fitness.plan.v2.line"].create(
                            {
                                "block_id": new_block.id,
                                "sequence": line.sequence,
                                "exercise_id": line.exercise_id.id,
                                "exercise_type": line.exercise_type,
                                "sets": line.sets,
                                "reps": line.reps,
                                "repetition_unit_id": line.repetition_unit_id.id,
                                "weight": line.weight,
                                "weight_unit_id": line.weight_unit_id.id,
                                "rir": line.rir,
                                "rest_seconds": line.rest_seconds,
                            }
                        )

                for activity in day.activity_ids.sorted("sequence"):
                    scheduled_date = self._compute_new_scheduled_date(
                        new_plan, phase, day
                    )
                    self.env["fitness.plan.v2.activity"].create(
                        {
                            "day_id": new_day.id,
                            "sequence": activity.sequence,
                            "exercise_id": activity.exercise_id.id,
                            "exercise_type": activity.exercise_type,
                            "sets": activity.sets,
                            "reps": activity.reps,
                            "repetition_unit_id": activity.repetition_unit_id.id,
                            "weight": activity.weight,
                            "weight_unit_id": activity.weight_unit_id.id,
                            "rir": activity.rir,
                            "rest_seconds": activity.rest_seconds,
                            "notes": activity.notes,
                            "scheduled_date": scheduled_date,
                        }
                    )

        return new_plan

    def _compute_new_scheduled_date(self, plan, phase, day):
        if plan.start and phase.start_offset:
            return plan.start + timedelta(
                weeks=(phase.start_offset - 1),
                days=(day.sequence - 1),
            )
        return False
