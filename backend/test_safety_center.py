"""End-to-end tests for DavidAI Safety Center dashboard."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from backend.safety_center_service import (
    get_location_history,
    get_recent_contacts,
    get_recent_notifications,
    get_recent_sos_alerts,
    get_safety_summary,
)
from database.models import SOSAlert, SOSNotification, TrustedContact, User


def _register(client, suffix: str) -> tuple[str, str]:
    email = f"safety{suffix}@davidai.local"
    password = "testpass123"
    client.post(
        "/register",
        data={
            "full_name": f"Safety User {suffix}",
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

    r = client.get("/safety-center")
    results.append(("Login required for /safety-center", r.status_code == 302, f"status={r.status_code}"))

    email_a, password_a = _register(client, f"a{stamp}")
    client.get("/logout", follow_redirects=True)
    email_b, password_b = _register(client, f"b{stamp}")
    results.append(("Register users A and B", True, f"{email_a} / {email_b}"))

    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_a, "password": password_a}, follow_redirects=True)

    client.post(
        "/contacts/add",
        data={
            "full_name": "Primary Partner",
            "phone_number": "07700900123",
            "email": "partner@example.com",
            "relationship": "Partner",
            "is_primary": "on",
        },
        follow_redirects=True,
    )
    client.post(
        "/contacts/add",
        data={
            "full_name": "Secondary Friend",
            "phone_number": "07700900456",
            "email": "",
            "relationship": "Friend",
        },
        follow_redirects=True,
    )

    client.post("/sos/trigger", json={"latitude": 51.5074, "longitude": -0.1278})
    client.post("/sos/trigger", json={"latitude": 53.48, "longitude": -2.24})

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        summary = get_safety_summary(user_a.id)
        summary_ok = (
            summary["total_contacts"] == 2
            and summary["primary_contact_name"] == "Primary Partner"
            and summary["total_sos_alerts"] >= 2
            and summary["total_notifications"] >= 1
        )
        results.append(
            (
                "get_safety_summary loads counts",
                summary_ok,
                f"contacts={summary['total_contacts']} sos={summary['total_sos_alerts']}",
            )
        )

        contacts = get_recent_contacts(user_a.id)
        contacts_ok = len(contacts) == 2 and any(c["is_primary"] for c in contacts)
        results.append(("get_recent_contacts loads", contacts_ok, f"count={len(contacts)}"))

        sos_rows = get_recent_sos_alerts(user_a.id)
        sos_ok = len(sos_rows) >= 2 and all(r.get("maps_url") for r in sos_rows if r["latitude"])
        results.append(("get_recent_sos_alerts loads", sos_ok, f"count={len(sos_rows)}"))

        notes = get_recent_notifications(user_a.id)
        notes_ok = len(notes) >= 1 and "contact_name" in notes[0]
        results.append(("get_recent_notifications loads", notes_ok, f"count={len(notes)}"))

        locations = get_location_history(user_a.id)
        loc_ok = len(locations) >= 2 and "maps.google.com" in (locations[0].get("maps_url") or "")
        results.append(("get_location_history loads", loc_ok, f"count={len(locations)}"))

    r = client.get("/safety-center")
    page_ok = r.status_code == 200 and all(
        section in r.data
        for section in (
            b"Safety Overview",
            b"Trusted Contacts",
            b"SOS History",
            b"SMS History",
            b"Notification Status",
            b"Location History",
        )
    )
    results.append(("GET /safety-center returns 200 with widgets", page_ok, f"status={r.status_code}"))

    widget_ok = (
        b"Primary Partner" in r.data
        and b"Manage Contacts" in r.data
        and b"View SOS Page" in r.data
        and b"maps.google.com" in r.data
    )
    results.append(("Dashboard displays widget content", widget_ok, "contacts+sos+maps"))

    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_b, "password": password_b}, follow_redirects=True)

    with app.app_context():
        user_b = db.session.scalar(db.select(User).filter_by(email=email_b))
        b_summary = get_safety_summary(user_b.id)
        b_contacts = get_recent_contacts(user_b.id)
        b_sos = db.session.scalars(db.select(SOSAlert).filter_by(user_id=user_b.id)).all()
        b_notes = db.session.scalars(db.select(SOSNotification).filter_by(user_id=user_b.id)).all()

    r_b = client.get("/safety-center")
    isolation_ok = (
        b_summary["total_contacts"] == 0
        and len(b_contacts) == 0
        and len(b_sos) == 0
        and len(b_notes) == 0
        and b"Primary Partner" not in r_b.data
        and r_b.status_code == 200
    )
    results.append(("User B isolation — no user A data", isolation_ok, f"b_contacts={b_summary['total_contacts']}"))

    client.get("/logout", follow_redirects=True)
    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        a_alerts = db.session.scalars(db.select(SOSAlert).filter_by(user_id=user_a.id)).all()
        user_b = db.session.scalar(db.select(User).filter_by(email=email_b))
        for alert in a_alerts:
            if alert.user_id != user_a.id:
                isolation_ok = False

    results.append(
        (
            "SOS alerts scoped by user_id in DB",
            all(a.user_id == user_a.id for a in a_alerts),
            f"user_a_alerts={len(a_alerts)}",
        )
    )

    print("DavidAI Safety Center — Test Report")
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
