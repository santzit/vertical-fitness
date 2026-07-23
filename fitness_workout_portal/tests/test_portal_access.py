import json

from odoo.tests.common import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestPortalWorkoutAccess(HttpCase):
    def setUp(self):
        super().setUp()
        self.base_url = self.env["ir.config_parameter"].get_param("web.base.url")

        self.trainer = self.env["res.users"].create({
            "login": "portal_trainer",
            "name": "Portal Trainer",
            "password": "test",
            "groups_id": [(4, self.env.ref("base.group_user").id)],
        })

        self.portal_user = self.env["res.users"].create({
            "login": "portal_member",
            "name": "Portal Member",
            "password": "test",
            "groups_id": [
                (4, self.env.ref("base.group_portal").id),
            ],
        })

        self.other_portal = self.env["res.users"].create({
            "login": "portal_other",
            "name": "Other Member",
            "password": "test",
            "groups_id": [
                (4, self.env.ref("base.group_portal").id),
            ],
        })

        self.partner = self.portal_user.partner_id

        self.user_routine = self.env["fitness.workout.plan"].sudo().create({
            "name": "My Routine",
            "description": "Test routine for portal",
            "plan_scope": "user",
            "partner_id": self.partner.id,
            "start": "2026-01-01",
            "end": "2026-03-31",
            "is_template": False,
            "is_public": False,
            "state": "active",
        })

        self.public_template = self.env["fitness.workout.plan"].sudo().create({
            "name": "Public Template",
            "description": "A public template",
            "plan_scope": "template",
            "partner_id": self.trainer.partner_id.id,
            "start": "2026-01-01",
            "end": "2026-06-30",
            "is_template": True,
            "is_public": True,
            "state": "active",
        })

        self.private_template = self.env["fitness.workout.plan"].sudo().create({
            "name": "Private Template",
            "description": "A private template",
            "plan_scope": "template",
            "partner_id": self.trainer.partner_id.id,
            "start": "2026-01-01",
            "end": "2026-06-30",
            "is_template": True,
            "is_public": False,
            "state": "active",
        })

        self.other_routine = self.env["fitness.workout.plan"].sudo().create({
            "name": "Other Routine",
            "plan_scope": "user",
            "partner_id": self.other_portal.partner_id.id,
            "start": "2026-01-01",
            "end": "2026-03-31",
            "is_template": False,
            "is_public": False,
            "state": "active",
        })

    def test_portal_user_sees_own_routines(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts")
        self.assertEqual(response.status_code, 200)
        self.assertIn("My Routine", response.text)

    def test_portal_user_sees_public_templates(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts")
        self.assertIn("Public Template", response.text)

    def test_portal_user_does_not_see_other_routines(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts")
        self.assertNotIn("Other Routine", response.text)

    def test_portal_user_does_not_see_private_templates(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts")
        self.assertNotIn("Private Template", response.text)

    def test_portal_user_can_access_own_routine_detail(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/routines/{self.user_routine.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("My Routine", response.text)

    def test_portal_user_cannot_access_other_routine_detail(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/routines/{self.other_routine.id}",
            head=False,
        )
        self.assertIn(response.status_code, [403, 404])

    def test_portal_user_can_access_public_template_detail(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/routines/{self.public_template.id}"
        )
        self.assertEqual(response.status_code, 200)

    def test_portal_user_cannot_access_private_template_detail(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/routines/{self.private_template.id}",
            head=False,
        )
        self.assertIn(response.status_code, [403, 404])

    def test_api_dashboard_returns_json(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertIn("total_routines", data)
        self.assertIn("active_routine", data)
        self.assertEqual(data["total_routines"], 1)

    def test_api_routines_returns_own_only(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(f"{self.base_url}/my/workouts/api/routines")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["name"], "My Routine")

    def test_api_routine_detail_own(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/api/routines/{self.user_routine.id}"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(data["name"], "My Routine")

    def test_api_routine_detail_other_returns_403(self):
        self.authenticate("portal_member", "test")
        response = self.url_open(
            f"{self.base_url}/my/workouts/api/routines/{self.other_routine.id}",
            head=False,
        )
        self.assertIn(response.status_code, [403, 404])

    def test_api_exercise_detail(self):
        exercise = self.env["fitness.exercise"].sudo().search([], limit=1)
        if exercise:
            self.authenticate("portal_member", "test")
            response = self.url_open(
                f"{self.base_url}/my/workouts/api/exercises/{exercise.id}"
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.text)
            self.assertIn("name", data)
