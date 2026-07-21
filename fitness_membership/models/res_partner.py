# Copyright 2025 SANTZ IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    membership_duration_text = fields.Char(
        compute="_compute_membership_duration_text",
        store=True,
    )
    membership_remaining_text = fields.Char(
        compute="_compute_membership_remaining_text",
        store=True,
    )

    @api.depends("membership_start", "membership_stop")
    def _compute_membership_duration_text(self):
        for partner in self:
            start = partner.membership_start
            stop = partner.membership_stop
            if not start or not stop or stop < start:
                partner.membership_duration_text = ""
                continue
            total_days = (stop - start).days + 1
            weeks, days = divmod(total_days, 7)
            if weeks:
                partner.membership_duration_text = (
                    f"{weeks} week{'s' if weeks != 1 else ''}, "
                    f"{days} day{'s' if days != 1 else ''}"
                )
            else:
                partner.membership_duration_text = (
                    f"{total_days} day{'s' if total_days != 1 else ''}"
                )

    @api.depends("membership_stop")
    def _compute_membership_remaining_text(self):
        today = fields.Date.context_today(self)
        for partner in self:
            stop = partner.membership_stop
            if not stop:
                partner.membership_remaining_text = ""
                continue
            delta = (today - stop).days
            if delta > 0:
                suffix = "s" if delta != 1 else ""
                partner.membership_remaining_text = (
                    f"Expired {delta} day{suffix} ago"
                )
            else:
                remaining = abs(delta)
                partner.membership_remaining_text = (
                    f"{remaining} day{'s' if remaining != 1 else ''} remaining"
                )
