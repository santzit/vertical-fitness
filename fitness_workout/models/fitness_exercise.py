import base64
import json
import uuid
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import api, fields, models


class FitnessExerciseCategory(models.Model):
    _name = "fitness.exercise.category"
    _description = "Exercise Category"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    wger_id = fields.Integer(index=True, copy=False)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    exercise_ids = fields.One2many(
        "fitness.exercise", "category_id", string="Exercises"
    )
    exercise_count = fields.Integer(compute="_compute_exercise_count")

    @api.depends("exercise_ids")
    def _compute_exercise_count(self):
        for rec in self:
            rec.exercise_count = len(rec.exercise_ids)

    _sql_constraints = [
        (
            "fitness_exercise_category_wger_id_uniq",
            "unique(wger_id)",
            "wger ID must be unique.",
        ),
    ]


class FitnessEquipment(models.Model):
    _name = "fitness.equipment"
    _description = "Equipment"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(required=True, translate=True)
    wger_id = fields.Integer(index=True, copy=False)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "fitness_equipment_wger_id_uniq",
            "unique(wger_id)",
            "wger ID must be unique.",
        ),
    ]


class FitnessMuscle(models.Model):
    _name = "fitness.muscle"
    _description = "Muscle"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        required=True,
        translate=True,
        help='In latin, e.g. "Pectoralis major"',
    )
    name_en = fields.Char(
        translate=True,
        help="A more basic name for the muscle",
    )
    wger_id = fields.Integer(index=True, copy=False)
    is_front = fields.Boolean(
        default=True,
        help="Whether the muscle is on the front of the body",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_muscle_wger_id_uniq", "unique(wger_id)", "wger ID must be unique."),
    ]


class FitnessExercise(models.Model):
    _name = "fitness.exercise"
    _description = "Exercise"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _order = "name"

    uuid = fields.Char(
        default=lambda self: str(uuid.uuid4()),
        readonly=True,
        copy=False,
        index=True,
    )
    wger_id = fields.Integer(index=True, copy=False)
    wger_image_url = fields.Char(copy=False)
    wger_image_synced_at = fields.Datetime(readonly=True, copy=False)
    wger_image_sync_status = fields.Selection(
        selection=[
            ("never", "Never synced"),
            ("ok", "Image synced"),
            ("missing", "No image on WGER"),
            ("error", "Sync error"),
        ],
        default="never",
        copy=False,
        tracking=True,
    )
    wger_image_sync_message = fields.Char(copy=False)
    name = fields.Char(required=True, translate=True, index=True)
    description = fields.Text(translate=True)
    category_id = fields.Many2one(
        "fitness.exercise.category",
        string="Category",
        required=True,
        ondelete="restrict",
    )
    muscle_ids = fields.Many2many(
        "fitness.muscle",
        "fitness_exercise_muscle_rel",
        "exercise_id",
        "muscle_id",
        string="Primary Muscles",
    )
    muscles_secondary_ids = fields.Many2many(
        "fitness.muscle",
        "fitness_exercise_muscle_secondary_rel",
        "exercise_id",
        "muscle_id",
        string="Secondary Muscles",
    )
    equipment_ids = fields.Many2many(
        "fitness.equipment",
        "fitness_exercise_equipment_rel",
        "exercise_id",
        "equipment_id",
        string="Equipment",
    )
    variation_group = fields.Char(help="UUID grouping exercise variations")
    video_url = fields.Char(help="YouTube or other video URL")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("fitness_exercise_uuid_uniq", "unique(uuid)", "Exercise UUID must be unique."),
        ("fitness_exercise_wger_id_uniq", "unique(wger_id)", "wger ID must be unique."),
    ]

    @api.depends("name", "category_id")
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name]
            if rec.category_id:
                parts.append(f"[{rec.category_id.name}]")
            rec.display_name = " ".join(parts)

    def action_sync_wger_image(self):
        for exercise in self:
            exercise._sync_single_wger_image()
        return True

    @api.model
    def action_import_wger_exercises(self, limit=200, sync_images=True):
        data = self._fetch_json(
            f"https://wger.de/api/v2/exerciseinfo/?{urlencode({'limit': limit})}"
        )
        results = data.get("results") or []
        created_or_updated = 0
        for item in results:
            category = self._get_or_create_wger_category(item.get("category"))
            if not category:
                continue
            vals = {
                "name": self._get_wger_translation_name(item)
                or f"Exercise {item.get('id')}",
                "description": self._get_wger_translation_description(item),
                "wger_id": item.get("id"),
                "variation_group": item.get("variation_group") or False,
                "category_id": category.id,
                "muscle_ids": [
                    (
                        6,
                        0,
                        self._get_or_create_wger_muscles(item.get("muscles") or []).ids,
                    )
                ],
                "muscles_secondary_ids": [
                    (
                        6,
                        0,
                        self._get_or_create_wger_muscles(
                            item.get("muscles_secondary") or []
                        ).ids,
                    )
                ],
                "equipment_ids": [
                    (
                        6,
                        0,
                        self._get_or_create_wger_equipment(
                            item.get("equipment") or []
                        ).ids,
                    )
                ],
            }
            exercise = self.search([("wger_id", "=", item.get("id"))], limit=1)
            if exercise:
                exercise.write(vals)
            else:
                exercise = self.create(vals)
            created_or_updated += 1

            images = item.get("images") or []
            main_image = next((img for img in images if img.get("is_main")), False)
            image_url = (main_image or (images[0] if images else {})).get("image")
            if image_url:
                exercise.write({"wger_image_url": image_url})
                if sync_images:
                    exercise._sync_single_wger_image()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "WGER import completed",
                "message": f"Imported or updated {created_or_updated} exercises.",
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def action_sync_wger_images_batch(self, limit=100):
        domain = [("wger_id", "!=", False), ("active", "=", True)]
        exercises = self.search(domain, limit=limit)
        for exercise in exercises:
            exercise._sync_single_wger_image()
        return True

    def _sync_single_wger_image(self):
        self.ensure_one()
        values = {
            "wger_image_synced_at": fields.Datetime.now(),
        }
        try:
            image_url = self._get_wger_image_url(self.wger_id)
            values["wger_image_url"] = image_url or False
        except Exception as exc:
            values.update(
                {
                    "wger_image_sync_status": "error",
                    "wger_image_sync_message": f"WGER request failed: {exc}",
                }
            )
            self.write(values)
            return
        if not image_url:
            values.update(
                {
                    "wger_image_sync_status": "missing",
                    "wger_image_sync_message": "No image returned by WGER.",
                }
            )
            self.write(values)
            return
        try:
            image_bytes = self._fetch_binary(image_url)
            values.update(
                {
                    "image_1920": base64.b64encode(image_bytes),
                    "wger_image_sync_status": "ok",
                    "wger_image_sync_message": "Image synced from WGER.",
                }
            )
        except Exception as exc:
            values.update(
                {
                    "wger_image_sync_status": "error",
                    "wger_image_sync_message": str(exc),
                }
            )
        self.write(values)

    @api.model
    def _fetch_json(self, url):
        request = Request(url, headers={"User-Agent": "Odoo fitness_workout"})
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    @api.model
    def _fetch_binary(self, url):
        request = Request(url, headers={"User-Agent": "Odoo fitness_workout"})
        with urlopen(request, timeout=30) as response:
            return response.read()

    @api.model
    def _get_wger_image_url(self, wger_id):
        if not wger_id:
            return False
        endpoints = [
            (
                "https://wger.de/api/v2/exerciseimage/",
                {"exercise": wger_id, "is_main": True, "limit": 1},
            ),
            (
                "https://wger.de/api/v2/exerciseimage/",
                {"exercise": wger_id, "limit": 1},
            ),
            (
                "https://wger.de/api/v2/exerciseimage/",
                {"exercise_base": wger_id, "is_main": True, "limit": 1},
            ),
            (
                "https://wger.de/api/v2/exerciseimage/",
                {"exercise_base": wger_id, "limit": 1},
            ),
        ]
        for base_url, params in endpoints:
            data = self._fetch_json(f"{base_url}?{urlencode(params)}")
            results = data.get("results") or []
            if not results:
                continue
            image_url = results[0].get("image") or results[0].get("url")
            if image_url:
                return image_url
        return False

    @api.model
    def _get_or_create_wger_category(self, category):
        if not category:
            return False
        wger_id = category.get("id") if isinstance(category, dict) else category
        name = (
            category.get("name")
            if isinstance(category, dict)
            else f"Category {wger_id}"
        )
        record = self.env["fitness.exercise.category"].search(
            [("wger_id", "=", wger_id)], limit=1
        )
        if not record:
            record = self.env["fitness.exercise.category"].create(
                {"name": name, "wger_id": wger_id}
            )
        elif name and record.name != name:
            record.name = name
        return record

    @api.model
    def _get_or_create_wger_muscles(self, muscles):
        model = self.env["fitness.muscle"]
        records = model.browse()
        for item in muscles:
            wger_id = item.get("id") if isinstance(item, dict) else item
            name = item.get("name") if isinstance(item, dict) else f"Muscle {wger_id}"
            name_en = item.get("name_en") if isinstance(item, dict) else False
            is_front = item.get("is_front", True) if isinstance(item, dict) else True
            rec = model.search([("wger_id", "=", wger_id)], limit=1)
            if not rec:
                rec = model.create(
                    {
                        "name": name,
                        "name_en": name_en,
                        "is_front": is_front,
                        "wger_id": wger_id,
                    }
                )
            records |= rec
        return records

    @api.model
    def _get_or_create_wger_equipment(self, equipment):
        model = self.env["fitness.equipment"]
        records = model.browse()
        for item in equipment:
            wger_id = item.get("id") if isinstance(item, dict) else item
            name = (
                item.get("name") if isinstance(item, dict) else f"Equipment {wger_id}"
            )
            rec = model.search([("wger_id", "=", wger_id)], limit=1)
            if not rec:
                rec = model.create({"name": name, "wger_id": wger_id})
            records |= rec
        return records

    @api.model
    def _get_wger_translation_name(self, item):
        translations = item.get("translations") or []
        preferred = next(
            (t for t in translations if t.get("language") == 2 and t.get("name")), False
        )
        if preferred:
            return preferred.get("name")
        first = next((t for t in translations if t.get("name")), False)
        return first.get("name") if first else False

    @api.model
    def _get_wger_translation_description(self, item):
        translations = item.get("translations") or []
        preferred = next(
            (
                t
                for t in translations
                if t.get("language") == 2 and t.get("description")
            ),
            False,
        )
        if preferred:
            return preferred.get("description")
        first = next((t for t in translations if t.get("description")), False)
        return first.get("description") if first else False
