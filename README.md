# DavidAI — Safety MVP

Safety-first AI platform: GPS, SOS, trusted contacts, and local AI chat.

## Authentication

PostgreSQL-backed auth with Flask-Login and Werkzeug password hashing.

| Feature | Status |
|---------|--------|
| User registration | Ready |
| Login / logout | Ready |
| Session management | Ready (Flask-Login, remember me) |
| User dashboard | Ready |
| GPS location sharing | Architecture ready |
| Trusted contacts | Models ready |
| SOS emergency button | UI scaffold |
| £3.99 subscription | Planned (Stripe) |

## Run DavidAI app

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI\backend
pip install -r requirements.txt
cd ..
.\run_migrations.ps1
cd backend
python app.py
```

Open http://127.0.0.1:5001 — register a new account or sign in.

## Database

- **Dev DB:** `davidai_dev`
- **Config:** `database/config.py` (`DAVIDAI_DATABASE_URL`)
- **Models:** `database/models.py`
- **Migrations:** `alembic upgrade head` from project root

## Navigation

- **Dashboard** — Account overview and quick actions
- **AI Chat** — Link to lab Ollama chat
- **Safety** — SOS and trusted contacts
- **Profile** — User details and subscription

## Structure

```
DavidAI/
├── backend/
│   ├── app.py           Flask app + auth routes
│   ├── extensions.py    db, login_manager
│   └── requirements.txt
├── database/
│   ├── config.py
│   ├── models.py
│   └── migrations/      Alembic
├── frontend/templates/
├── alembic.ini
└── run_migrations.ps1
```

## Related

- AI Lab Dashboard: http://127.0.0.1:5000/projects/davidai
- Safety docs: `docs/SAFETY_ARCHITECTURE.md`
