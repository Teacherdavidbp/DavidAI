"""DavidAI database configuration — environment-driven."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

_davidai_database_url = os.environ.get("DAVIDAI_DATABASE_URL")
if not _davidai_database_url:
    raise RuntimeError(
        "DAVIDAI_DATABASE_URL is not set. "
        "Copy .env.example to .env and set your PostgreSQL connection string."
    )

DATABASES = {
    "davidai": {
        "url": _davidai_database_url,
        "name": "davidai_dev",
    },
    "ai_quest": {
        "url": os.environ.get("AI_QUEST_DATABASE_URL", ""),
        "name": "ai_quest_dev",
    },
    "stem_academy": {
        "url": os.environ.get("STEM_DATABASE_URL", ""),
        "name": "stem_academy_dev",
    },
    "research_ai": {
        "url": os.environ.get("RESEARCH_AI_DATABASE_URL", ""),
        "name": "research_ai_dev",
    },
    "paintmemodels": {
        "url": os.environ.get("PAINTME_DATABASE_URL", ""),
        "name": "paintmemodels_dev",
    },
}

DEFAULT_DATABASE = os.environ.get("DATABASE_KEY", "davidai")
SQLALCHEMY_DATABASE_URI = DATABASES[DEFAULT_DATABASE]["url"]
SQLALCHEMY_TRACK_MODIFICATIONS = False
