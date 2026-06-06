"""Safety Center — aggregated safety data for the dashboard."""

from __future__ import annotations

from backend.extensions import db
from backend.notification_service import STATUS_SENT
from database.models import SOSAlert, SOSNotification, TrustedContact

DEFAULT_SOS_LIMIT = 10
DEFAULT_NOTIFICATION_LIMIT = 10
DEFAULT_LOCATION_LIMIT = 20
MESSAGE_PREVIEW_LEN = 120


def _maps_url(latitude: float | None, longitude: float | None) -> str | None:
    if latitude is None or longitude is None:
        return None
    return f"https://maps.google.com/?q={latitude},{longitude}"


def _truncate_message(message: str | None, limit: int = MESSAGE_PREVIEW_LEN) -> str:
    text = (message or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def contact_to_dict(contact: TrustedContact) -> dict:
    return {
        "id": contact.id,
        "full_name": contact.full_name,
        "relationship": contact.relationship,
        "phone_number": contact.phone_number,
        "email": contact.email,
        "is_primary": contact.is_primary,
    }


def alert_to_row(alert: SOSAlert) -> dict:
    lat = alert.latitude
    lng = alert.longitude
    return {
        "id": alert.id,
        "status": alert.status,
        "latitude": lat,
        "longitude": lng,
        "created_at": alert.created_at,
        "created_at_iso": alert.created_at.isoformat() if alert.created_at else None,
        "maps_url": _maps_url(lat, lng),
    }


def notification_to_row(notification: SOSNotification) -> dict:
    contact = notification.contact
    return {
        "id": notification.id,
        "contact_name": contact.full_name if contact else "Unknown",
        "channel": notification.channel,
        "status": notification.status,
        "message": notification.message,
        "message_preview": _truncate_message(notification.message),
        "created_at": notification.created_at,
        "created_at_iso": notification.created_at.isoformat() if notification.created_at else None,
    }


def location_to_row(alert: SOSAlert) -> dict:
    lat = alert.latitude
    lng = alert.longitude
    return {
        "id": alert.id,
        "latitude": lat,
        "longitude": lng,
        "created_at": alert.created_at,
        "created_at_iso": alert.created_at.isoformat() if alert.created_at else None,
        "maps_url": _maps_url(lat, lng),
    }


def get_safety_summary(user_id: int) -> dict:
    total_contacts = db.session.scalar(
        db.select(db.func.count()).select_from(TrustedContact).filter_by(user_id=user_id)
    ) or 0

    primary = db.session.scalar(
        db.select(TrustedContact).filter_by(user_id=user_id, is_primary=True)
    )

    total_sos = db.session.scalar(
        db.select(db.func.count()).select_from(SOSAlert).filter_by(user_id=user_id)
    ) or 0

    active_sos = db.session.scalar(
        db.select(db.func.count())
        .select_from(SOSAlert)
        .filter_by(user_id=user_id, status="active")
    ) or 0

    total_notifications = db.session.scalar(
        db.select(db.func.count()).select_from(SOSNotification).filter_by(user_id=user_id)
    ) or 0

    sms_sent = db.session.scalar(
        db.select(db.func.count())
        .select_from(SOSNotification)
        .filter_by(user_id=user_id, status=STATUS_SENT)
    ) or 0

    return {
        "total_contacts": total_contacts,
        "primary_contact_name": primary.full_name if primary else None,
        "primary_contact_id": primary.id if primary else None,
        "total_sos_alerts": total_sos,
        "active_sos_alerts": active_sos,
        "total_notifications": total_notifications,
        "sms_sent_count": sms_sent,
    }


def get_recent_contacts(user_id: int) -> list[dict]:
    contacts = db.session.scalars(
        db.select(TrustedContact)
        .filter_by(user_id=user_id)
        .order_by(TrustedContact.is_primary.desc(), TrustedContact.full_name.asc())
    ).all()
    return [contact_to_dict(c) for c in contacts]


def get_recent_sos_alerts(user_id: int, limit: int = DEFAULT_SOS_LIMIT) -> list[dict]:
    alerts = db.session.scalars(
        db.select(SOSAlert)
        .filter_by(user_id=user_id)
        .order_by(SOSAlert.created_at.desc())
        .limit(limit)
    ).all()
    return [alert_to_row(a) for a in alerts]


def get_recent_notifications(user_id: int, limit: int = DEFAULT_NOTIFICATION_LIMIT) -> list[dict]:
    notes = db.session.scalars(
        db.select(SOSNotification)
        .filter_by(user_id=user_id)
        .order_by(SOSNotification.created_at.desc())
        .limit(limit)
    ).all()
    return [notification_to_row(n) for n in notes]


def get_location_history(user_id: int, limit: int = DEFAULT_LOCATION_LIMIT) -> list[dict]:
    alerts = db.session.scalars(
        db.select(SOSAlert)
        .filter_by(user_id=user_id)
        .order_by(SOSAlert.created_at.desc())
        .limit(limit)
    ).all()
    return [location_to_row(a) for a in alerts]
