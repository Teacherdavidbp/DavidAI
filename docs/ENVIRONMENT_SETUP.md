# DavidAI Environment Setup

## Where `.env` lives

```
C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI\.env
```

Copy from `.env.example` if you do not have one yet:

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI
Copy-Item .env.example .env
```

Do not commit `.env` to git.

---

## Required variables

| Variable | Purpose |
|----------|---------|
| `DAVIDAI_DATABASE_URL` | PostgreSQL connection to `davidai_dev` |
| `DAVIDAI_SECRET_KEY` | Flask session signing secret |

### `DAVIDAI_DATABASE_URL`

Format:

```
DAVIDAI_DATABASE_URL=postgresql+psycopg2://postgres:<YOUR_POSTGRES_PASSWORD>@localhost:5432/davidai_dev
```

Use the same PostgreSQL password as your lab setup (see `05_DATABASES\PostgreSQL\dashboard.env` for reference).

### `DAVIDAI_SECRET_KEY`

Use a long random string. Generate one in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the output into `.env`:

```
DAVIDAI_SECRET_KEY=<generated-value>
```

---

## Verify configuration

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI
python -m pip install -r backend/requirements.txt
python backend/check_config.py
```

Expected output ends with `OVERALL: PASS`.

---

## Run migrations

After `check_config.py` passes:

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI
.\run_migrations.ps1
```

This loads `.env` and runs `alembic upgrade head` against `davidai_dev`.

---

## Start the app

```powershell
cd C:\AI-LAB-DPEDTECH-LTD\03_PROJECTS\DavidAI\backend
python app.py
```

Open http://127.0.0.1:5001

The app loads `.env` automatically via `python-dotenv` on startup.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `DAVIDAI_DATABASE_URL is not set` | Create `.env` from `.env.example` |
| Password authentication failed | Update password in `DAVIDAI_DATABASE_URL` |
| Database does not exist | Run `05_DATABASES\PostgreSQL\Scripts\create_all_databases.sql` |
| `OVERALL: FAIL` from check_config | Fix the failing checks before running migrations |
