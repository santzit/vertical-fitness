import logging

from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class PortalWorkoutHome(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if "workout_routine_count" in counters:
            values["workout_routine_count"] = (
                request.env["fitness.workout.plan"]
                .sudo()
                .search_count(
                    [
                        ("plan_scope", "=", "user"),
                        ("partner_id", "=", partner.id),
                        ("active", "=", True),
                    ]
                )
            )

        if "workout_template_count" in counters:
            values["workout_template_count"] = (
                request.env["fitness.workout.plan"]
                .sudo()
                .search_count(
                    [
                        ("plan_scope", "=", "template"),
                        ("partner_id", "=", partner.id),
                        ("active", "=", True),
                    ]
                )
            )

        if "workout_public_template_count" in counters:
            values["workout_public_template_count"] = (
                request.env["fitness.workout.plan"]
                .sudo()
                .search_count(
                    [
                        ("plan_scope", "=", "template"),
                        ("is_public", "=", True),
                        ("active", "=", True),
                    ]
                )
            )

        if "workout_exercise_count" in counters:
            values["workout_exercise_count"] = (
                request.env["fitness.exercise"]
                .sudo()
                .search_count([("active", "=", True)])
            )

        return values
