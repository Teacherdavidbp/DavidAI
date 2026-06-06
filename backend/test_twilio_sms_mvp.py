"""Tests for Twilio SMS integration — mocked client only, no real SMS."""

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from backend.notification_service import create_sos_notification
from backend.sms_service import (
    SmsDeliveryResult,
    is_twilio_ready,
    normalize_phone_e164,
    sanitize_provider_detail,
    send_twilio_sms,
)
from database.models import SOSAlert, SOSNotification, TrustedContact, User


def _clear_twilio_env() -> None:
    for key in (
        "TWILIO_ENABLED",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER",
    ):
        os.environ.pop(key, None)


def _set_twilio_env(enabled: bool = True, complete: bool = True) -> None:
    _clear_twilio_env()
    os.environ["TWILIO_ENABLED"] = "true" if enabled else "false"
    if complete:
        os.environ["TWILIO_ACCOUNT_SID"] = "ACtestaccountsid0000000000000000"
        os.environ["TWILIO_AUTH_TOKEN"] = "testauthtoken"
        os.environ["TWILIO_FROM_NUMBER"] = "+15551234567"


def _mock_twilio_success():
    message = MagicMock()
    message.sid = "SMmock1234567890abcdef"

    client = MagicMock()
    client.messages.create.return_value = message

    def factory(account_sid, auth_token):
        return client

    return factory, client


def _mock_twilio_failure():
    client = MagicMock()
    client.messages.create.side_effect = Exception(
        "HTTP 401 error: AuthToken=secretvalue invalid"
    )

    def factory(account_sid, auth_token):
        return client

    return factory, client


def run_tests() -> int:
    _clear_twilio_env()
    app = create_app()
    results: list[tuple[str, bool, str]] = []
    stamp = str(int(time.time()))

    # --- sms_service unit tests ---
    results.append(
        (
            "is_twilio_ready false when disabled",
            not is_twilio_ready(),
            "default env",
        )
    )

    _set_twilio_env(enabled=True, complete=True)
    results.append(
        (
            "is_twilio_ready true when configured",
            is_twilio_ready(),
            "all vars set",
        )
    )

    _set_twilio_env(enabled=True, complete=False)
    os.environ.pop("TWILIO_AUTH_TOKEN", None)
    results.append(
        (
            "is_twilio_ready false when credentials missing",
            not is_twilio_ready(),
            "missing auth token",
        )
    )

    results.append(
        (
            "normalize UK mobile to E.164",
            normalize_phone_e164("07700 900 001") == "+447700900001",
            normalize_phone_e164("07700 900 001"),
        )
    )

    sanitized = sanitize_provider_detail("AuthToken=supersecret ACabc123")
    results.append(
        (
            "sanitize_provider_detail redacts secrets",
            sanitized is not None and "supersecret" not in sanitized and "[redacted]" in sanitized,
            sanitized or "",
        )
    )

    _clear_twilio_env()
    simulated = send_twilio_sms("+447700900001", "test body")
    results.append(
        (
            "send_twilio_sms simulated when disabled",
            simulated.status == "simulated",
            simulated.provider_detail or "",
        )
    )

    _set_twilio_env(enabled=True, complete=True)
    factory, client = _mock_twilio_success()
    sent = send_twilio_sms("+447700900001", "SOS test", client_factory=factory)
    results.append(
        (
            "send_twilio_sms sent with mocked client",
            sent.status == "sent" and sent.provider_sid == "SMmock1234567890abcdef",
            sent.provider_sid or "",
        )
    )
    results.append(
        (
            "mocked Twilio client called once",
            client.messages.create.call_count == 1,
            f"calls={client.messages.create.call_count}",
        )
    )

    factory_fail, client_fail = _mock_twilio_failure()
    failed = send_twilio_sms("+447700900001", "SOS fail", client_factory=factory_fail)
    results.append(
        (
            "send_twilio_sms failed with mocked error",
            failed.status == "failed" and "secretvalue" not in (failed.provider_detail or ""),
            failed.provider_detail or "",
        )
    )

    # --- notification integration tests ---
    _clear_twilio_env()
    client_http = app.test_client()
    email = f"twilio{stamp}@davidai.local"
    password = "testpass123"
    client_http.post(
        "/register",
        data={
            "full_name": "Twilio User",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    client_http.post(
        "/contacts/add",
        data={
            "full_name": "SMS Contact",
            "phone_number": "07700900002",
            "email": "sms@example.com",
            "relationship": "Partner",
            "is_primary": "on",
        },
        follow_redirects=True,
    )

    r = client_http.post(
        "/sos/trigger",
        json={"latitude": 51.5, "longitude": -0.12},
    )
    data = r.get_json() or {}
    notif = data.get("notification") or {}
    results.append(
        (
            "SOS trigger simulated notification",
            r.status_code == 200 and notif.get("status") == "simulated",
            notif.get("status", ""),
        )
    )

    with app.app_context():
        user = db.session.scalar(db.select(User).filter_by(email=email))
        contact = db.session.scalar(
            db.select(TrustedContact).filter_by(user_id=user.id, is_primary=True)
        )
        alert = db.session.scalar(
            db.select(SOSAlert).filter_by(user_id=user.id).order_by(SOSAlert.id.desc())
        )

        def mock_sent(phone, body):
            return SmsDeliveryResult(
                status="sent",
                provider_sid="SMintegrationtest",
                provider_detail="Mock delivery OK",
            )

        note_sent, _ = create_sos_notification(
            user.id,
            alert.id,
            sms_sender=mock_sent,
        )
        sent_ok = note_sent is not None and note_sent.status == "sent"
        results.append(
            (
                "create_sos_notification status sent (mock)",
                sent_ok,
                note_sent.status if note_sent else "none",
            )
        )

        def mock_failed(phone, body):
            return SmsDeliveryResult(
                status="failed",
                provider_detail="Mock Twilio error",
            )

        note_failed, _ = create_sos_notification(
            user.id,
            alert.id,
            sms_sender=mock_failed,
        )
        failed_ok = note_failed is not None and note_failed.status == "failed"
        results.append(
            (
                "create_sos_notification status failed (mock)",
                failed_ok,
                note_failed.status if note_failed else "none",
            )
        )

        contact.phone_number = ""
        db.session.commit()

        def should_not_run(phone, body):
            raise AssertionError("SMS sender must not run without phone")

        note_no_phone, _ = create_sos_notification(
            user.id,
            alert.id,
            sms_sender=should_not_run,
        )
        no_phone_ok = note_no_phone is not None and note_no_phone.status == "failed"
        results.append(
            (
                "create_sos_notification failed without phone",
                no_phone_ok,
                note_no_phone.provider_detail if note_no_phone else "",
            )
        )

    r_page = client_http.get("/sos")
    page_ok = (
        r_page.status_code == 200
        and b"SMS mode:" in r_page.data
        and b"badge-sos-sent" in r_page.data
    )
    results.append(
        (
            "GET /sos shows SMS status badges",
            page_ok,
            f"status={r_page.status_code}",
        )
    )

    _clear_twilio_env()

    print("DavidAI Twilio SMS MVP — Test Report")
    print("=" * 50)
    passed = 0
    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"[{status}] {name} — {detail}")
    print("=" * 50)
    print(f"OVERALL: {'PASS' if passed == len(results) else 'FAIL'} ({passed}/{len(results)})")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(run_tests())
