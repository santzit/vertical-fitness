import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _json_response(data, status=200):
    payload = json.dumps(data, default=str)
    resp = request.make_response(
        payload,
        headers={
            "Content-Type": "application/json",
        },
    )
    resp.status = str(status)
    return resp


def _get_int(value, default=None):
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class PortalWorkoutApiController(http.Controller):
    @http.route(
        "/my/workouts/api/dashboard",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def api_dashboard(self, **kwargs):
        partner = request.env.user.partner_id
        routines = (
            request.env["fitness.workout.plan"]
            .sudo()
            .search(
                [
                    ("plan_scope", "=", "user"),
                    ("partner_id", "=", partner.id),
                    ("active", "=", True),
                ]
            )
        )
        active_routine = routines[:1]
        recent_exercises = (
            request.env["fitness.exercise"]
            .sudo()
            .search([("active", "=", True)], limit=10, order="write_date desc")
        )
        data = {
            "total_routines": len(routines),
            "active_routine": (
                _serialize_routine_brief(active_routine) if active_routine else None
            ),
            "recent_exercises": [
                {
                    "id": e.id,
                    "name": e.name or "",
                    "category": e.category_id.name if e.category_id else "",
                    "image_url": (
                        f"/web/image/fitness.exercise/{e.id}/image_128"
                        if e.image_1920
                        else None
                    ),
                }
                for e in recent_exercises
            ],
        }
        return _json_response(data)

    @http.route(
        "/my/workouts/api/routines",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def api_routines(self, **kwargs):
        partner = request.env.user.partner_id
        limit = _get_int(kwargs.get("limit"), 50)
        offset = _get_int(kwargs.get("offset"), 0)
        domain = [
            ("plan_scope", "=", "user"),
            ("partner_id", "=", partner.id),
            ("active", "=", True),
        ]
        plans = (
            request.env["fitness.workout.plan"]
            .sudo()
            .search(domain, limit=limit, offset=offset, order="start desc")
        )
        total = request.env["fitness.workout.plan"].sudo().search_count(domain)
        return _json_response(
            {
                "count": total,
                "next": None,
                "previous": None,
                "results": [_serialize_routine_brief(p) for p in plans],
            }
        )

    @http.route(
        "/my/workouts/api/routines/<int:routine_id>",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def api_routine_detail(self, routine_id, **kwargs):
        partner = request.env.user.partner_id
        plan = request.env["fitness.workout.plan"].sudo().browse(routine_id)
        if not plan.exists():
            return _json_response({"detail": "Not found"}, status=404)
        if plan.plan_scope == "user" and plan.partner_id.id != partner.id:
            return _json_response({"detail": "Forbidden"}, status=403)
        if plan.plan_scope == "template" and not plan.is_public:
            return _json_response({"detail": "Forbidden"}, status=403)
        return _json_response(_serialize_routine_detail(plan))

    @http.route(
        "/my/workouts/api/exercises/<int:exercise_id>",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def api_exercise_detail(self, exercise_id, **kwargs):
        exercise = request.env["fitness.exercise"].sudo().browse(exercise_id)
        if not exercise.exists():
            return _json_response({"detail": "Not found"}, status=404)
        return _json_response(_serialize_exercise(exercise))


def _serialize_routine_brief(plan):
    if not plan:
        return None
    return {
        "id": plan.id,
        "name": plan.name or "",
        "description": plan.description or "",
        "start": str(plan.start) if plan.start else None,
        "end": str(plan.end) if plan.end else None,
        "duration_text": plan.duration_text or "",
        "state": plan.state or "draft",
        "day_count": len(plan.day_ids),
        "is_template": plan.plan_scope == "template",
        "is_public": bool(plan.is_public),
    }


def _serialize_routine_detail(plan):
    data = _serialize_routine_brief(plan)
    data["days"] = [_serialize_day(day) for day in plan.day_ids.sorted("sequence")]
    return data


def _serialize_day(day):
    return {
        "id": day.id,
        "name": day.name or "",
        "description": day.description or "",
        "sequence": day.sequence,
        "start_offset": day.start_offset,
        "end_offset": day.end_offset,
        "slots": [_serialize_slot(slot) for slot in day.slot_ids.sorted("sequence")],
    }


def _serialize_slot(slot):
    entries = []
    for card in slot.card_ids.sorted("sequence"):
        entries.append(_serialize_card(card))
    for block in slot.block_ids.sorted("sequence"):
        for entry in block.entry_ids.sorted("sequence"):
            entries.append(_serialize_entry(entry, block))
    return {
        "id": slot.id,
        "name": slot.name or "",
        "slot_type": slot.slot_type or "custom",
        "is_rest": bool(slot.is_rest),
        "notes": slot.notes or "",
        "board_title": slot.board_title or slot.name or "",
        "board_prescription": slot.board_prescription or "",
        "entries": entries,
    }


def _serialize_card(card):
    return {
        "id": card.id,
        "exercise_id": card.exercise_id.id,
        "exercise_name": card.exercise_id.name or "",
        "exercise_type": card.exercise_type or "normal",
        "sets": card.sets,
        "reps": card.reps,
        "repetition_unit": (
            card.repetition_unit_id.name if card.repetition_unit_id else ""
        ),
        "weight": card.weight,
        "weight_unit": card.weight_unit_id.name if card.weight_unit_id else "",
        "rir": card.rir,
        "rest_seconds": card.rest_seconds,
        "notes": card.notes or "",
    }


def _serialize_entry(entry, block=None):
    return {
        "id": entry.id,
        "exercise_id": entry.exercise_id.id,
        "exercise_name": entry.exercise_id.name or "",
        "exercise_type": entry.exercise_type or "normal",
        "sets": entry.sets,
        "reps": entry.reps,
        "repetition_unit": (
            entry.repetition_unit_id.name if entry.repetition_unit_id else ""
        ),
        "weight": entry.weight,
        "weight_unit": entry.weight_unit_id.name if entry.weight_unit_id else "",
        "rir": entry.rir,
        "rest_seconds": entry.rest_seconds,
        "block_name": block.name if block else "",
        "block_type": block.block_type if block else "",
    }


def _serialize_exercise(exercise):
    images = []
    media_items = exercise.media_ids.filtered("active").sorted(
        key=lambda media: (not media.is_primary, media.id)
    )
    for media in media_items:
        images.append(
            {
                "id": media.id,
                "url": f"/web/image/ir.attachment/{media.attachment_id.id}/datas",
                "is_primary": bool(media.is_primary),
                "style": media.wger_style or "",
            }
        )
    if not images and exercise.image_1920:
        images.append(
            {
                "id": exercise.id,
                "url": f"/web/image/fitness.exercise/{exercise.id}/image_1920",
                "is_primary": True,
                "style": "",
            }
        )
    return {
        "id": exercise.id,
        "name": exercise.name or "",
        "description": exercise.description or "",
        "category": {
            "id": exercise.category_id.id,
            "name": exercise.category_id.name or "",
        }
        if exercise.category_id
        else None,
        "muscles": [
            {"id": m.id, "name": m.name or "", "is_front": bool(m.is_front)}
            for m in exercise.muscle_ids
        ],
        "muscles_secondary": [
            {"id": m.id, "name": m.name or "", "is_front": bool(m.is_front)}
            for m in exercise.muscles_secondary_ids
        ],
        "equipment": [
            {"id": e.id, "name": e.name or ""} for e in exercise.equipment_ids
        ],
        "images": images,
        "video_url": exercise.video_url or None,
    }
