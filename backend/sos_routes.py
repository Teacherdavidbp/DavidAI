"""SOS alert routes — Phase 1 GPS capture and storage."""

import logging

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.sos_service import (
    alert_to_dict,
    get_user_alert,
    list_active_alerts,
    list_resolved_alerts,
    resolve_alert,
    trigger_alert,
    validate_coordinates,
)

logger = logging.getLogger(__name__)


def register_sos_routes(app: Flask) -> None:
    @app.route("/sos")
    @login_required
    def sos_page():
        active = list_active_alerts(current_user.id)
        history = list_resolved_alerts(current_user.id)
        return render_template(
            "sos.html",
            page="sos",
            active_alerts=active,
            alert_history=history,
        )

    @app.route("/sos/trigger", methods=["POST"])
    @login_required
    def sos_trigger():
        body = request.get_json(silent=True) or {}
        latitude = body.get("latitude")
        longitude = body.get("longitude")

        ok, error = validate_coordinates(latitude, longitude)
        if not ok:
            logger.warning("SOS trigger validation failed user=%s error=%s", current_user.id, error)
            return jsonify({"ok": False, "error": error}), 400

        alert = trigger_alert(current_user.id, float(latitude), float(longitude))
        logger.info(
            "SOS triggered user=%s alert_id=%s lat=%s lng=%s",
            current_user.id,
            alert.id,
            alert.latitude,
            alert.longitude,
        )
        return jsonify({"ok": True, "alert": alert_to_dict(alert)})

    @app.route("/sos/resolve/<int:alert_id>", methods=["POST"])
    @login_required
    def sos_resolve(alert_id: int):
        wants_json = (
            request.is_json
            or request.headers.get("Accept", "").startswith("application/json")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )

        alert = get_user_alert(current_user.id, alert_id)
        if alert is None:
            if wants_json:
                return jsonify({"ok": False, "error": "Alert not found."}), 404
            flash("Alert not found.", "error")
            return redirect(url_for("sos_page"))

        if alert.status == "resolved":
            message = "This alert is already resolved."
            if wants_json:
                return jsonify({"ok": False, "error": message}), 400
            flash(message, "warning")
            return redirect(url_for("sos_page"))

        resolve_alert(alert)
        logger.info("SOS resolved user=%s alert_id=%s", current_user.id, alert.id)

        if wants_json:
            return jsonify({"ok": True, "alert": alert_to_dict(alert)})

        flash("SOS alert marked as resolved.", "success")
        return redirect(url_for("sos_page"))
