"""Twilio SMS delivery for SOS alerts — credentials from .env only."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SECRET_PATTERNS = (
    re.compile(r"SK[a-z0-9]{32}", re.I),
    re.compile(r"AC[a-z0-9]{32}", re.I),
    re.compile(r"AuthToken[=:\s]+[^\s]+", re.I),
)


@dataclass
class SmsDeliveryResult:
    status: str
    provider_sid: str | None = None
    provider_detail: str | None = None


def _env_bool(name: str, default: bool = False) -> bool:
    value = (os.environ.get(name) or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def get_twilio_config() -> dict[str, str | bool]:
    return {
        "enabled": _env_bool("TWILIO_ENABLED", False),
        "account_sid": (os.environ.get("TWILIO_ACCOUNT_SID") or "").strip(),
        "auth_token": (os.environ.get("TWILIO_AUTH_TOKEN") or "").strip(),
        "from_number": (os.environ.get("TWILIO_FROM_NUMBER") or "").strip(),
    }


def is_twilio_ready() -> bool:
    cfg = get_twilio_config()
    return bool(
        cfg["enabled"]
        and cfg["account_sid"]
        and cfg["auth_token"]
        and cfg["from_number"]
    )


def twilio_mode_label() -> str:
    if is_twilio_ready():
        return "live"
    cfg = get_twilio_config()
    if cfg["enabled"]:
        return "misconfigured"
    return "simulated"


def sanitize_provider_detail(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = str(text)
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned[:500]


def normalize_phone_e164(phone: str) -> str:
    """Basic UK-friendly normalization for lab contacts."""
    compact = re.sub(r"[\s\-()]", "", phone.strip())
    if compact.startswith("+"):
        return compact
    if compact.startswith("00"):
        return "+" + compact[2:]
    if compact.startswith("0") and len(compact) >= 10:
        return "+44" + compact[1:]
    if compact.startswith("44"):
        return "+" + compact
    return compact


def send_twilio_sms(
    to_phone: str,
    body: str,
    *,
    client_factory=None,
) -> SmsDeliveryResult:
    """Send SMS via Twilio, or return simulated when disabled."""
    if not is_twilio_ready():
        return SmsDeliveryResult(
            status="simulated",
            provider_detail="Twilio disabled or credentials missing — simulated SMS only.",
        )

    destination = normalize_phone_e164(to_phone)
    if not destination.startswith("+") or len(destination) < 8:
        return SmsDeliveryResult(
            status="failed",
            provider_detail="Primary contact phone number is not a valid SMS destination.",
        )

    cfg = get_twilio_config()
    try:
        if client_factory is not None:
            client = client_factory(cfg["account_sid"], cfg["auth_token"])
        else:
            from twilio.rest import Client

            client = Client(cfg["account_sid"], cfg["auth_token"])

        message = client.messages.create(
            body=body,
            from_=cfg["from_number"],
            to=destination,
        )
        sid = getattr(message, "sid", None)
        logger.info("Twilio SMS sent sid=%s to=***%s", sid, destination[-4:])
        return SmsDeliveryResult(
            status="sent",
            provider_sid=sid,
            provider_detail=f"Delivered via Twilio to {destination[-4:].rjust(len(destination), '*')}",
        )
    except Exception as exc:
        detail = sanitize_provider_detail(str(exc)) or "Twilio SMS delivery failed."
        logger.warning("Twilio SMS failed: %s", detail)
        return SmsDeliveryResult(status="failed", provider_detail=detail)
