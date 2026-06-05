# DavidAI Database

**Database:** `davidai_dev`  
**Config:** `database/config.py`  
**Models:** `database/models.py`  
**Migrations:** `database/migrations/`

## Setup

1. Ensure PostgreSQL is running and `davidai_dev` exists:

```powershell
# From lab database scripts (if not already created)
psql -U postgres -f C:\AI-LAB-DPEDTECH-LTD\05_DATABASES\PostgreSQL\Scripts\create_all_databases.sql
```

2. Install dependencies:

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI\backend
pip install -r requirements.txt
```

3. Run migrations:

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI
alembic upgrade head
```

Or use the helper script:

```powershell
.\run_migrations.ps1
```

## Environment

Copy `.env.example` to `.env` and set `DAVIDAI_DATABASE_URL` if your credentials differ from the default.

Default connection:

```
postgresql+psycopg2://postgres:postgres@localhost:5432/davidai_dev
```

## Tables

| Table | Purpose |
|-------|---------|
| `users` | Authentication (email, password_hash, full_name) |
| `trusted_contacts` | Emergency contact list per user |
| `sos_alerts` | GPS SOS events |
| `subscriptions` | Stripe billing (planned) |

## Create a new migration

After changing models:

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
