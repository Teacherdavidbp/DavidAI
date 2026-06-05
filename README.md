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
| GPS location sharing | Architecture ready |
| Trusted contacts | Models ready |
| SOS emergency button | UI scaffold |
| £3.99 subscription | Planned (Stripe) |

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
- **Models:** `database/models.py` — includes `conversations`, `messages`
- **Migrations:** `alembic upgrade head` from project root

## Navigation

- **Dashboard** — Account overview and quick actions
- **AI Chat** — Local Qwen chat with history
- **Safety** — SOS and trusted contacts
- **Profile** — User details and subscription

## Structure

```
DavidAI/
├── backend/
│   ├── app.py           Flask app + auth + chat routes
│   ├── chat_service.py  Ollama + mock web search
│   ├── chat_routes.py   Conversation storage
│   └── requirements.txt
├── database/
│   ├── config.py
│   ├── models.py
│   └── migrations/
├── frontend/templates/
├── frontend/static/js/chat.js
└── run_migrations.ps1
```

## Related

- AI Lab Dashboard: http://127.0.0.1:5000/projects/davidai
- Safety docs: `docs/SAFETY_ARCHITECTURE.md`
