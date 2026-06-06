"""SOS notification foundation — simulated SMS only (no Twilio/email)."""

from __future__ import annotations

from datetime import datetime

from backend.extensions import db
from database.models import SOSAlert, SOSNotification, TrustedContact, User

CHANNEL_SMS = "sms"
STATUS_SIMULATED = "simulated"
NO_PRIMARY_WARNING = "SOS created, but no primary trusted contact is set."


def get_primary_contact_for_user(user_id: int) -> TrustedContact | None:
    return db.session.scalar(
        db.select(TrustedContact).filter_by(user_id=user_id, is_primary=True)
    )


def build_sos_message(
    user_email: str,
    triggered_at: datetime,
    latitude: float,
    longitude: float,
) -> str:
    timestamp = triggered_at.strftime("%Y-%m-%d %H:%M UTC")
    maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
    return (
        f"DavidAI SOS Alert: {user_email} triggered an SOS alert at {timestamp}. "
        f"Location: {maps_url}"
    )


def create_sos_notification(
    user_id: int,
    sos_alert_id: int,
) -> tuple[SOSNotification | None, str | None]:
    """Create a simulated SMS notification if a primary contact exists."""
    contact = get_primary_contact_for_user(user_id)
    if contact is None:
        return None, NO_PRIMARY_WARNING

    user = db.session.get(User, user_id)
    alert = db.session.scalar(
        db.select(SOSAlert).filter_by(id=sos_alert_id, user_id=user_id)
    )
    if user is None or alert is None:
        return None, "SOS alert not found."

    message = build_sos_message(
        user.email,
        alert.created_at or datetime.utcnow(),
        float(alert.latitude or 0),
        float(alert.longitude or 0),
    )

    notification = SOSNotification(
        user_id=user_id,
        sos_alert_id=sos_alert_id,
        contact_id=contact.id,
        channel=CHANNEL_SMS,
        status=STATUS_SIMULATED,
        message=message,
    )
    db.session.add(notification)
    db.session.commit()
    db.session.refresh(notification)
    return notification, None


def list_user_notifications(user_id: int) -> list[SOSNotification]:
    return list(
        db.session.scalars(
            db.select(SOSNotification)
            .filter_by(user_id=user_id)
            .order_by(SOSNotification.created_at.desc())
        ).all()
    )


def notification_to_dict(notification: SOSNotification) -> dict:
    contact = notification.contact
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "sos_alert_id": notification.sos_alert_id,
        "contact_id": notification.contact_id,
        "contact_name": contact.full_name if contact else "Unknown",
        "channel": notification.channel,
        "status": notification.status,
        "message": notification.message,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
    }
