"""End-to-end test for DavidAI AI Chat MVP."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.extensions import db
from database.models import Conversation, Message, User


def run_tests() -> int:
    app = create_app()
    results: list[tuple[str, bool, str]] = []

    client = app.test_client()
    email = f"chattest{int(__import__('time').time())}@davidai.local"
    password = "testpass123"

    # Register
    r = client.post(
        "/register",
        data={
            "full_name": "Chat Tester",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    results.append(("Register user", r.status_code == 200, f"status={r.status_code}"))

    # Access /chat while logged in
    r = client.get("/chat")
    results.append(("GET /chat", r.status_code == 200, f"status={r.status_code}"))

    # Send hello
    r = client.post(
        "/api/chat",
        json={"message": "hello", "use_web_search": False},
    )
    data = r.get_json() or {}
    ok = r.status_code == 200 and data.get("ok") and data.get("message")
    results.append(("POST /api/chat hello", ok, data.get("message", data.get("error", r.status_code))[:80]))

    # Check DB
    with app.app_context():
        user = db.session.scalar(db.select(User).filter_by(email=email))
        conv = db.session.scalar(db.select(Conversation).filter_by(user_id=user.id))
        msgs = db.session.scalars(db.select(Message).filter_by(conversation_id=conv.id)).all()
        db_ok = conv is not None and len(msgs) == 2
        results.append(
            ("Messages saved in davidai_dev",
             db_ok,
             f"conversation_id={conv.id if conv else None} messages={len(msgs)}"),
        )

    # Logout
    r = client.get("/logout", follow_redirects=True)
    results.append(("Logout", r.status_code == 200, f"status={r.status_code}"))

    # Login again
    r = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    results.append(("Login again", r.status_code == 200, f"status={r.status_code}"))

    # History persists
    r = client.get("/api/conversations")
    hist = r.get_json() or {}
    hist_ok = hist.get("ok") and len(hist.get("messages", [])) == 2
    results.append(
        ("History after re-login",
         hist_ok,
         f"messages={len(hist.get('messages', []))}"),
    )

    print("DavidAI AI Chat MVP — Test Report")
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
