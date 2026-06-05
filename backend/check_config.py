"""Verify DavidAI environment and database connectivity."""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ENV_PATH = PROJECT_ROOT / ".env"
PLACEHOLDER_SECRETS = {
    "",
    "change-me-in-production",
    "<change_me_to_a_strong_secret>",
    "<CHANGE_ME_TO_A_STRONG_SECRET>",
}


def mask_database_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    database = parsed.path.lstrip("/") or "unknown"
    return f"postgresql+psycopg2://{user}:***@{host}:{port}/{database}"


def check(name: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    return passed


def main() -> int:
    print("DavidAI configuration check")
    print("=" * 40)

    results: list[bool] = []

    results.append(check(".env file exists", ENV_PATH.is_file(), str(ENV_PATH)))

    load_dotenv(ENV_PATH)

    database_url = os.environ.get("DAVIDAI_DATABASE_URL", "").strip()
    secret_key = os.environ.get("DAVIDAI_SECRET_KEY", "").strip()

    results.append(
        check(
            "DAVIDAI_DATABASE_URL set",
            bool(database_url),
            "missing from .env" if not database_url else mask_database_url(database_url),
        )
    )

    secret_valid = bool(secret_key) and secret_key.lower() not in PLACEHOLDER_SECRETS
    results.append(
        check(
            "DAVIDAI_SECRET_KEY set",
            secret_valid,
            "configured" if secret_valid else "missing or placeholder value",
        )
    )

    db_name = ""
    if database_url:
        db_name = urlparse(database_url).path.lstrip("/")
        results.append(
            check(
                "Database name is davidai_dev",
                db_name == "davidai_dev",
                db_name or "could not parse database name",
            )
        )

    if database_url and db_name == "davidai_dev":
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as conn:
                current_db = conn.execute(text("SELECT current_database()")).scalar()
            results.append(
                check(
                    "PostgreSQL connection",
                    current_db == "davidai_dev",
                    f"connected to {current_db}",
                )
            )
        except Exception as exc:
            message = str(exc).splitlines()[0]
            if "password authentication failed" in message:
                detail = "password authentication failed"
            elif "could not connect" in message.lower():
                detail = "could not connect to server"
            else:
                detail = message[:120]
            results.append(check("PostgreSQL connection", False, detail))
    else:
        results.append(check("PostgreSQL connection", False, "skipped — invalid DATABASE_URL"))

    print("=" * 40)
    if all(results):
        print("OVERALL: PASS")
        return 0

    print("OVERALL: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
