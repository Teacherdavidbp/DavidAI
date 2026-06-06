"""Safety Center routes — central hub for safety activity."""

import logging

from flask import Flask, render_template
from flask_login import current_user, login_required

from backend.safety_center_service import (
    get_location_history,
    get_recent_contacts,
    get_recent_notifications,
    get_recent_sos_alerts,
    get_safety_summary,
)
from backend.sms_service import twilio_mode_label

logger = logging.getLogger(__name__)

SMS_HISTORY_LIMIT = 20


def register_safety_center_routes(app: Flask) -> None:
    @app.route("/safety-center")
    @login_required
    def safety_center():
        user_id = current_user.id
        summary = get_safety_summary(user_id)
        contacts = get_recent_contacts(user_id)
        sos_alerts = get_recent_sos_alerts(user_id)
        sms_history = get_recent_notifications(user_id, limit=SMS_HISTORY_LIMIT)
        notification_status = get_recent_notifications(user_id, limit=10)
        locations = get_location_history(user_id)

        logger.info(
            "Safety Center loaded user=%s contacts=%s sos=%s notifications=%s",
            user_id,
            summary["total_contacts"],
            summary["total_sos_alerts"],
            summary["total_notifications"],
        )

        return render_template(
            "safety_center.html",
            page="safety_center",
            summary=summary,
            contacts=contacts,
            sos_alerts=sos_alerts,
            sms_history=sms_history,
            notification_status=notification_status,
            locations=locations,
            twilio_mode=twilio_mode_label(),
        )
