"""End-to-end tests for SOS Trusted Contact Notifications MVP."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from backend.notification_service import NO_PRIMARY_WARNING
from database.models import SOSAlert, SOSNotification, TrustedContact, User


def _register(client, suffix: str) -> tuple[str, str]:
    email = f"notif{suffix}@davidai.local"
    password = "testpass123"
    client.post(
        "/register",
        data={
            "full_name": f"Notify User {suffix}",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    return email, password


def run_tests() -> int:
    app = create_app()
    results: list[tuple[str, bool, str]] = []
    client = app.test_client()
    stamp = str(int(time.time()))

    email_a, password_a = _register(client, f"a{stamp}")
    results.append(("Login (register user A)", True, email_a))

    client.post(
        "/contacts/add",
        data={
            "full_name": "Primary Contact",
            "phone_number": "07700900001",
            "email": "primary@example.com",
            "relationship": "Partner",
            "is_primary": "on",
        },
        follow_redirects=True,
    )

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        primary = db.session.scalar(
            db.select(TrustedContact).filter_by(user_id=user_a.id, is_primary=True)
        )
        has_primary = primary is not None and primary.full_name == "Primary Contact"
    results.append(("Create and set primary contact", has_primary, f"primary_id={primary.id if primary else None}"))

    r = client.post(
        "/sos/trigger",
        json={"latitude": 51.5074, "longitude": -0.1278},
    )
    data = r.get_json() or {}
    notif_data = data.get("notification")
    trigger_ok = r.status_code == 200 and data.get("ok") and notif_data
    results.append(("Trigger SOS with notification", trigger_ok, str(notif_data or data.get("warning"))))

    alert_id = data.get("alert", {}).get("id")
    notif_id = notif_data.get("id") if notif_data else None

    with app.app_context():
        note = db.session.get(SOSNotification, notif_id) if notif_id else None
        db_ok = (
            note is not None
            and note.channel == "sms"
            and note.status == "simulated"
            and note.sos_alert_id == alert_id
        )
        results.append(
            ("SOSNotification in PostgreSQL",
             db_ok,
             f"channel={note.channel if note else None} status={note.status if note else None}"),
        )

    maps_ok = "maps.google.com/?q=51.5074,-0.1278" in (notif_data or {}).get("message", "")
    results.append(("Message contains Google Maps link", maps_ok, (notif_data or {}).get("message", "")[:80]))

    r = client.post(
        "/sos/trigger",
        json={"latitude": 53.0, "longitude": -1.0},
    )
    data2 = r.get_json() or {}
    second_ok = data2.get("ok") and data2.get("notification") is not None
    results.append(("Second SOS also creates notification", second_ok, "ok"))

    client.get("/logout", follow_redirects=True)
    email_b, _ = _register(client, f"b{stamp}")

    r = client.post(
        "/sos/trigger",
        json={"latitude": 52.0, "longitude": 0.5},
    )
    data_b = r.get_json() or {}
    warning_ok = data_b.get("ok") and data_b.get("warning") == NO_PRIMARY_WARNING
    results.append(("No primary contact returns warning", warning_ok, data_b.get("warning", "")))

    with app.app_context():
        user_b = db.session.scalar(db.select(User).filter_by(email=email_b))
        b_notes = db.session.scalars(
            db.select(SOSNotification).filter_by(user_id=user_b.id)
        ).all()
        no_notif = len(b_notes) == 0
    results.append(("No notification without primary contact", no_notif, f"count={len(b_notes)}"))

    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_a, "password": password_a}, follow_redirects=True)

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        a_notes = list(
            db.session.scalars(db.select(SOSNotification).filter_by(user_id=user_a.id)).all()
        )

    r = client.get("/sos")
    isolation_ok = r.status_code == 200 and b"Notification history" in r.data
    results.append(("GET /sos with notification history", isolation_ok, f"user_a_notes={len(a_notes)}"))

    print("DavidAI SOS Notifications MVP — Test Report")
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
