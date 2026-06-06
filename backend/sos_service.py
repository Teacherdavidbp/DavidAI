"""SOS alert business logic — Phase 1 (store GPS, no notifications)."""

from __future__ import annotations

from datetime import datetime

from backend.extensions import db
from database.models import SOSAlert

STATUS_ACTIVE = "active"
STATUS_RESOLVED = "resolved"
VALID_STATUSES = {STATUS_ACTIVE, STATUS_RESOLVED}


def validate_coordinates(latitude: float | None, longitude: float | None) -> tuple[bool, str]:
    if latitude is None or longitude is None:
        return False, "GPS coordinates are required. Enable location access and try again."

    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return False, "Invalid GPS coordinates received."

    if not (-90 <= lat <= 90):
        return False, "Latitude must be between -90 and 90."
    if not (-180 <= lng <= 180):
        return False, "Longitude must be between -180 and 180."

    return True, ""


def list_user_alerts(user_id: int) -> list[SOSAlert]:
    return list(
        db.session.scalars(
            db.select(SOSAlert)
            .filter_by(user_id=user_id)
            .order_by(SOSAlert.created_at.desc())
        ).all()
    )


def list_active_alerts(user_id: int) -> list[SOSAlert]:
    return list(
        db.session.scalars(
            db.select(SOSAlert)
            .filter_by(user_id=user_id, status=STATUS_ACTIVE)
            .order_by(SOSAlert.created_at.desc())
        ).all()
    )


def list_resolved_alerts(user_id: int) -> list[SOSAlert]:
    return list(
        db.session.scalars(
            db.select(SOSAlert)
            .filter_by(user_id=user_id, status=STATUS_RESOLVED)
            .order_by(SOSAlert.created_at.desc())
        ).all()
    )


def get_user_alert(user_id: int, alert_id: int) -> SOSAlert | None:
    return db.session.scalar(
        db.select(SOSAlert).filter_by(id=alert_id, user_id=user_id)
    )


def trigger_alert(user_id: int, latitude: float, longitude: float) -> SOSAlert:
    alert = SOSAlert(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        status=STATUS_ACTIVE,
    )
    db.session.add(alert)
    db.session.commit()
    db.session.refresh(alert)
    return alert


def resolve_alert(alert: SOSAlert) -> SOSAlert:
    if alert.status == STATUS_RESOLVED:
        return alert
    alert.status = STATUS_RESOLVED
    alert.resolved_at = datetime.utcnow()
    db.session.commit()
    db.session.refresh(alert)
    return alert


def alert_to_dict(alert: SOSAlert) -> dict:
    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "latitude": alert.latitude,
        "longitude": alert.longitude,
        "status": alert.status,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }
