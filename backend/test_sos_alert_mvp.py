"""End-to-end tests for DavidAI SOS Alert MVP Phase 1."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from database.models import SOSAlert, User


def _register(client, suffix: str) -> tuple[str, str]:
    email = f"sos{suffix}@davidai.local"
    password = "testpass123"
    client.post(
        "/register",
        data={
            "full_name": f"SOS User {suffix}",
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

    r = client.get("/sos")
    results.append(("GET /sos", r.status_code == 200, f"status={r.status_code}"))

    r = client.post("/sos/trigger", json={})
    data = r.get_json() or {}
    results.append(
        ("Trigger rejects missing coordinates",
         r.status_code == 400 and not data.get("ok"),
         data.get("error", r.status_code)),
    )

    r = client.post(
        "/sos/trigger",
        json={"latitude": 51.5074, "longitude": -0.1278},
    )
    data = r.get_json() or {}
    trigger_ok = r.status_code == 200 and data.get("ok") and data.get("alert", {}).get("id")
    results.append(("Trigger SOS with GPS", trigger_ok, str(data.get("alert", data.get("error")))))

    alert_id = data.get("alert", {}).get("id") if trigger_ok else 0

    with app.app_context():
        user_a = db.session.scalar(db.select(User).filter_by(email=email_a))
        alert = db.session.get(SOSAlert, alert_id) if alert_id else None
        db_ok = (
            alert is not None
            and alert.user_id == user_a.id
            and alert.status == "active"
            and alert.latitude == 51.5074
            and alert.longitude == -0.1278
        )
        results.append(
            ("PostgreSQL record saved",
             db_ok,
             f"id={alert_id} status={alert.status if alert else None}"),
        )

    r = client.post(f"/sos/resolve/{alert_id}", follow_redirects=True)
    with app.app_context():
        alert = db.session.get(SOSAlert, alert_id)
        resolved_ok = alert is not None and alert.status == "resolved" and alert.resolved_at is not None
    results.append(("Resolve SOS", r.status_code == 200 and resolved_ok, f"status={alert.status if alert else None}"))

    client.get("/logout", follow_redirects=True)
    _register(client, f"b{stamp}")

    r = client.post(f"/sos/resolve/{alert_id}", follow_redirects=True)
    isolation_ok = b"not found" in r.data.lower() or b"Alert not found" in r.data
    results.append(("User B cannot resolve user A alert", isolation_ok, f"status={r.status_code}"))

    with app.app_context():
        alert = db.session.get(SOSAlert, alert_id)
        still_resolved = alert is not None and alert.status == "resolved"
    results.append(("User A alert unchanged after isolation test", still_resolved, f"status={alert.status if alert else None}"))

    client.get("/logout", follow_redirects=True)
    r = client.post(
        "/sos/trigger",
        json={"latitude": 52.0, "longitude": 0.5},
        follow_redirects=False,
    )
    results.append(("Not logged in blocked", r.status_code in (302, 401, 403), f"status={r.status_code}"))

    print("DavidAI SOS Alert MVP — Test Report")
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
