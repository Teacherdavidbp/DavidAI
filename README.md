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
| AI Chat MVP | Ready |
| Trusted Contacts MVP | Ready |
| GPS location sharing | Architecture ready |
| SOS emergency button | UI scaffold |
| £3.99 subscription | Planned (Stripe) |

## Trusted Contacts (`/contacts`)

Logged-in users can manage emergency contacts stored in PostgreSQL.

| Feature | Details |
|---------|---------|
| Add / edit / delete | Form-based CRUD |
| Primary contact | One primary per user; badge in UI |
| Validation | Full name required; phone or email required |
| Security | Flask-Login; users see only their own contacts |

### Routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/contacts` | Trusted contacts page |
| POST | `/contacts/add` | Add contact |
| POST | `/contacts/edit/<id>` | Edit contact |
| POST | `/contacts/delete/<id>` | Delete contact |
| POST | `/contacts/set-primary/<id>` | Set primary contact |

Test report: `docs/TRUSTED_CONTACTS_MVP_TEST_REPORT.md`

## AI Chat (`/chat`)

Local Qwen chat powered by Ollama, with optional mock web search.

| Feature | Details |
|---------|---------|
| Default model | `qwen2.5:7b` |
| Web search toggle | Off = normal Qwen; On = mock search context first |
| Chat storage | PostgreSQL `conversations` + `messages` tables |
| Access | Logged-in users only (Flask-Login) |

### API routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/chat` | Chat page |
| POST | `/api/chat` | Send message, get Qwen response, save to DB |
| GET | `/api/conversations` | Load user's chat history |
| POST | `/api/conversations/clear` | Clear user's chat history |

### Web search mode

Mock/test mode only — same pattern as AI-Lab-Dashboard. No API keys configured.

Future provider options: Tavily, Brave Search API, Serper, Google Custom Search.

### Error handling

- Ollama not running
- Model not installed (`ollama pull qwen2.5:7b`)
- Request timeout (180s backend, 195s frontend)
- Web search unavailable

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

Requires Ollama running with `qwen2.5:7b` installed.

## Database

- **Dev DB:** `davidai_dev`
- **Config:** `database/config.py` (`DAVIDAI_DATABASE_URL`)
- **Models:** `database/models.py` — `users`, `trusted_contacts`, `conversations`, `messages`
- **Migrations:** `alembic upgrade head` from project root (includes `003_trusted_contacts`)

## Navigation

- **Dashboard** — Account overview and quick actions
- **AI Chat** — Local Qwen chat with history
- **Safety** — SOS overview
- **Trusted Contacts** — Manage emergency contacts
- **Profile** — User details and subscription

## Structure

```
DavidAI/
├── backend/
│   ├── app.py
│   ├── chat_service.py
│   ├── chat_routes.py
│   ├── contacts_service.py
│   ├── contacts_routes.py
│   └── test_trusted_contacts_mvp.py
├── database/
│   ├── config.py
│   ├── models.py
│   └── migrations/
├── frontend/templates/contacts.html
├── docs/TRUSTED_CONTACTS_MVP_PLAN.md
└── run_migrations.ps1
```

## Related

- AI Lab Dashboard: http://127.0.0.1:5000/projects/davidai
- Safety docs: `docs/SAFETY_ARCHITECTURE.md`
