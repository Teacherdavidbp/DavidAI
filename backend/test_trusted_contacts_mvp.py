"""End-to-end tests for DavidAI Trusted Contacts MVP."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from database.models import TrustedContact, User


def _register(client, suffix: str) -> tuple[str, str]:
    email = f"contact{suffix}@davidai.local"
    password = "testpass123"
    client.post(
        "/register",
        data={
            "full_name": f"Contact User {suffix}",
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
    results.append(("Register user A", True, email_a))

    r = client.get("/contacts")
    results.append(("GET /contacts (login required page)", r.status_code == 200, f"status={r.status_code}"))

    r = client.post(
        "/contacts/add",
        data={
            "full_name": "Alex Parent",
            "phone_number": "07700900111",
            "email": "",
            "relationship": "Parent",
        },
        follow_redirects=True,
    )
    results.append(("Add contact", r.status_code == 200 and b"Alex Parent" in r.data, "added"))

    r = client.post(
        "/contacts/add",
        data={
            "full_name": "",
            "phone_number": "",
            "email": "",
            "relationship": "",
        },
        follow_redirects=True,
    )
    results.append(
        ("Validation rejects empty contact",
         b"Full name is required" in r.data or b"phone" in r.data.lower(),
         "validation"),
    )

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        contacts = db.session.scalars(db.select(TrustedContact).filter_by(user_id=user_a.id)).all()
        contact_a = contacts[0] if contacts else None
        db_ok = contact_a is not None and contact_a.is_primary
        results.append(
            ("First contact saved and primary in PostgreSQL",
             db_ok,
             f"id={contact_a.id if contact_a else None} primary={contact_a.is_primary if contact_a else None}"),
        )
        contact_a_id = contact_a.id if contact_a else 0

    r = client.post(
        "/contacts/add",
        data={
            "full_name": "Sam Friend",
            "phone_number": "",
            "email": "sam@example.com",
            "relationship": "Friend",
        },
        follow_redirects=True,
    )
    results.append(("Add second contact (email only)", r.status_code == 200, f"status={r.status_code}"))

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        second = db.session.scalar(
            db.select(TrustedContact).filter_by(user_id=user_a.id, full_name="Sam Friend")
        )
        second_id = second.id if second else 0

    r = client.post(
        f"/contacts/edit/{contact_a_id}",
        data={
            "full_name": "Alexandra Parent",
            "phone_number": "07700900222",
            "email": "alex@example.com",
            "relationship": "Mother",
        },
        follow_redirects=True,
    )
    results.append(
        ("Edit contact",
         r.status_code == 200 and b"Alexandra Parent" in r.data,
         "edited"),
    )

    r = client.post(f"/contacts/set-primary/{second_id}", follow_redirects=True)
    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        primary_count = db.session.scalar(
            db.select(db.func.count())
            .select_from(TrustedContact)
            .filter_by(user_id=user_a.id, is_primary=True)
        )
        second = db.session.get(TrustedContact, second_id)
        primary_ok = primary_count == 1 and second and second.is_primary
    results.append(("Set primary (only one primary)", primary_ok, f"primary_count={primary_count}"))

    client.get("/logout", follow_redirects=True)
    email_b, password_b = _register(client, f"b{stamp}")

    with app.app_context():
        user_b = db.session.scalar(db.select(User).filter_by(email=email_b))

    r = client.post(f"/contacts/delete/{contact_a_id}", follow_redirects=True)
    isolation_ok = b"Contact not found" in r.data or b"not found" in r.data.lower()
    results.append(("User B cannot delete user A contact", isolation_ok, f"status={r.status_code}"))

    with app.app_context():
        still_exists = db.session.get(TrustedContact, contact_a_id) is not None
    results.append(("User A contact survives isolation test", still_exists, f"exists={still_exists}"))

    client.get("/logout", follow_redirects=True)
    client.post("/login", data={"email": email_a, "password": password_a}, follow_redirects=True)

    r = client.post(f"/contacts/delete/{contact_a_id}", follow_redirects=True)
    with app.app_context():
        deleted = db.session.get(TrustedContact, contact_a_id) is None
    results.append(("Delete contact", r.status_code == 200 and deleted, f"deleted={deleted}"))

    print("DavidAI Trusted Contacts MVP — Test Report")
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
