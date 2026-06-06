"""SOS notifications — simulated or Twilio SMS delivery."""

from __future__ import annotations

from datetime import datetime

from backend.extensions import db
from backend.sms_service import SmsDeliveryResult, send_twilio_sms, twilio_mode_label
from database.models import SOSAlert, SOSNotification, TrustedContact, User

CHANNEL_SMS = "sms"
STATUS_PENDING = "pending"
STATUS_SIMULATED = "simulated"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
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


def _apply_delivery_result(
    notification: SOSNotification,
    result: SmsDeliveryResult,
) -> None:
    notification.status = result.status
    notification.provider_sid = result.provider_sid
    notification.provider_detail = result.provider_detail
    notification.updated_at = datetime.utcnow()


def dispatch_sms_notification(
    notification: SOSNotification,
    contact: TrustedContact,
    message: str,
    *,
    sms_sender=send_twilio_sms,
) -> SOSNotification:
    """Attempt Twilio delivery or keep simulated fallback."""
    if not contact.phone_number:
        _apply_delivery_result(
            notification,
            SmsDeliveryResult(
                status=STATUS_FAILED,
                provider_detail="Primary contact has no phone number for SMS.",
            ),
        )
        db.session.commit()
        db.session.refresh(notification)
        return notification

    result = sms_sender(contact.phone_number, message)
    _apply_delivery_result(notification, result)
    db.session.commit()
    db.session.refresh(notification)
    return notification


def create_sos_notification(
    user_id: int,
    sos_alert_id: int,
    *,
    sms_sender=send_twilio_sms,
) -> tuple[SOSNotification | None, str | None]:
    """Create SOS notification and deliver SMS when Twilio is enabled."""
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
        status=STATUS_PENDING,
        message=message,
    )
    db.session.add(notification)
    db.session.commit()
    db.session.refresh(notification)

    notification = dispatch_sms_notification(
        notification,
        contact,
        message,
        sms_sender=sms_sender,
    )
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
        "provider_sid": notification.provider_sid,
        "provider_detail": notification.provider_detail,
        "twilio_mode": twilio_mode_label(),
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
    }
