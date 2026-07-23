from markupsafe import Markup

from odoo import http, tools
from odoo.http import request


class PortalWorkoutController(http.Controller):

    @http.route(
        ["/my/workouts", "/my/workouts/routines"],
        type="http",
        auth="user",
        website=True,
        sitemap=True,
    )
    def portal_routines(self, **kwargs):
        partner = request.env.user.partner_id
        routines = (
            request.env["fitness.workout.plan"]
            .sudo()
            .search([
                ("plan_scope", "=", "user"),
                ("partner_id", "=", partner.id),
                ("active", "=", True),
            ])
        )
        values = {
            "page_name": "workouts",
            "routines": routines,
            "partner": partner,
        }
        return request.render(
            "fitness_workout_portal.portal_routines_page", values
        )

    @http.route(
        "/my/workouts/routines/<int:routine_id>",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def portal_routine_detail(self, routine_id, **kwargs):
        partner = request.env.user.partner_id
        plan = request.env["fitness.workout.plan"].sudo().browse(routine_id)
        if not plan.exists():
            return request.not_found()
        if plan.plan_scope == "user" and plan.partner_id.id != partner.id:
            return request.not_found()
        if plan.plan_scope == "template" and not plan.is_public:
            return request.not_found()
        values = {
            "page_name": "workout_detail",
            "plan": plan,
            "days": plan.day_ids.sorted("sequence"),
            "partner": partner,
        }
        return request.render(
            "fitness_workout_portal.portal_routine_detail_page", values
        )

    @http.route(
        "/my/workouts/templates",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def portal_templates(self, **kwargs):
        partner = request.env.user.partner_id
        scope = kwargs.get("scope", "your")
        if scope == "public":
            templates = (
                request.env["fitness.workout.plan"]
                .sudo()
                .search([
                    ("plan_scope", "=", "template"),
                    ("is_public", "=", True),
                    ("active", "=", True),
                ])
            )
        else:
            templates = (
                request.env["fitness.workout.plan"]
                .sudo()
                .search([
                    ("plan_scope", "=", "template"),
                    ("partner_id", "=", partner.id),
                    ("active", "=", True),
                ])
            )
        values = {
            "page_name": "templates",
            "templates": templates,
            "scope": scope,
            "partner": partner,
        }
        return request.render(
            "fitness_workout_portal.portal_templates_page", values
        )

    @http.route(
        ["/my/exercises", "/my/workouts/exercises"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def portal_exercises(self, **kwargs):
        if request.httprequest.path == "/my/workouts/exercises":
            query_string = request.httprequest.query_string.decode()
            target = "/my/exercises"
            if query_string:
                target = f"{target}?{query_string}"
            return request.redirect(target, code=301)

        category_id = kwargs.get("category_id")
        domain = [("active", "=", True)]
        if category_id:
            try:
                domain.append(("category_id", "=", int(category_id)))
            except (ValueError, TypeError):
                pass
        exercises = (
            request.env["fitness.exercise"]
            .sudo()
            .search(domain, order="name")
        )
        categories = (
            request.env["fitness.exercise.category"]
            .sudo()
            .search([], order="name")
        )
        values = {
            "page_name": "exercises",
            "exercises": exercises,
            "categories": categories,
            "selected_category": int(category_id) if category_id else None,
        }
        return request.render(
            "fitness_workout_portal.portal_exercises_page", values
        )

    @http.route(
        ["/my/exercises/<int:exercise_id>", "/my/workouts/exercises/<int:exercise_id>"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def portal_exercise_detail(self, exercise_id, **kwargs):
        if request.httprequest.path.startswith("/my/workouts/exercises/"):
            return request.redirect(f"/my/exercises/{exercise_id}", code=301)

        exercise = request.env["fitness.exercise"].sudo().browse(exercise_id)
        if not exercise.exists():
            return request.not_found()
        description = (
            exercise.description or exercise.with_context(lang="en_US").description
        )
        description_html = Markup(tools.html_sanitize(description or ""))
        exercise_media = exercise.media_ids.filtered("active").sorted(
            key=lambda media: (not media.is_primary, media.id)
        )
        values = {
            "page_name": "exercise_detail",
            "exercise": exercise,
            "exercise_description_html": description_html,
            "exercise_media": exercise_media,
        }
        return request.render(
            "fitness_workout_portal.portal_exercise_detail_page", values
        )
