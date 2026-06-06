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
| SOS Alert MVP (Phase 1) | Ready |
| SOS Notifications MVP (Phase 2) | Ready — simulated SMS |
| Twilio SMS MVP | Ready — live SMS when enabled |
| Safety Center | Ready — unified safety dashboard |
| GPS location sharing | Browser geolocation on SOS trigger |
| Real SMS (Twilio) | Ready when `TWILIO_ENABLED=true` |
| Email notifications | Planned |
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

## Safety Center (`/safety-center`)

Central hub for reviewing and managing all safety-related activity. Existing pages (`/contacts`, `/sos`, `/safety`) remain unchanged.

| Widget | Contents |
|--------|----------|
| Safety Overview | Contact count, primary contact, SOS totals, notification totals, SMS sent |
| Trusted Contacts | All contacts with primary badge → **Manage Contacts** (`/contacts`) |
| SOS History | Latest alerts with map links → **View SOS Page** (`/sos`) |
| SMS History | Notification records with sent/failed/simulated/pending status |
| Notification Status | Last 10 notifications with message preview |
| Location History | Last 20 SOS GPS coordinates (history only, no live tracking) |

### Route

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/safety-center` | Safety Center dashboard (login required) |

Docs: `docs/SAFETY_CENTER_ARCHITECTURE.md` · Tests: `docs/SAFETY_CENTER_TEST_REPORT.md`

## SOS Alerts (`/sos`) — Phase 1

Logged-in users can trigger an SOS alert with browser GPS coordinates. Alerts are stored in PostgreSQL. **Phase 2** creates a simulated SMS notification for the primary trusted contact — no real SMS or email is sent.

| Feature | Details |
|---------|---------|
| Trigger | SOS button requests geolocation, POSTs to `/sos/trigger` |
| Storage | `sos_alerts` table — user_id, lat/lng, status, timestamps |
| Resolve | Mark active alerts as resolved |
| Security | Flask-Login; users see only their own alerts |

### Routes

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/sos` | SOS page — button, GPS status, active + history |
| POST | `/sos/trigger` | Create active alert (JSON: latitude, longitude) |
| POST | `/sos/resolve/<id>` | Resolve alert |

On trigger with a primary trusted contact, a `sos_notifications` record is created (`channel=sms`) with status `sent`, `failed`, or `simulated` depending on Twilio configuration. Message includes a Google Maps link.

Docs: `docs/SOS_ALERT_MVP_PLAN.md` · `docs/SOS_NOTIFICATIONS_MVP_PLAN.md` · `docs/TWILIO_SMS_MVP_TEST_REPORT.md`  
Tests: `docs/SOS_ALERT_MVP_TEST_REPORT.md` · `docs/SOS_NOTIFICATIONS_MVP_TEST_REPORT.md`

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
- **Safety Center** — Unified safety dashboard (contacts, SOS, SMS, locations)
- **Safety** — Legacy safety overview page
- **SOS Alerts** — Trigger and manage GPS SOS alerts
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
│   ├── sos_service.py
│   ├── sos_routes.py
│   ├── notification_service.py
│   ├── sms_service.py
│   ├── safety_center_service.py
│   ├── safety_center_routes.py
│   ├── test_trusted_contacts_mvp.py
│   ├── test_sos_alert_mvp.py
│   ├── test_sos_notifications_mvp.py
│   ├── test_twilio_sms_mvp.py
│   └── test_safety_center.py
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
