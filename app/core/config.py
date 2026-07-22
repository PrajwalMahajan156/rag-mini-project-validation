"""
Application configuration loaded exclusively from environment variables.

All sensitive values (API keys, secrets) must be supplied via the process
environment or a .env file.  This module validates required variables at
import time so the application fails fast with a clear message rather than
producing cryptic runtime errors deep inside a request handler.

Copy .env.example to .env and fill in real values before running locally.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Required environment variable validation
# ---------------------------------------------------------------------------

_REQUIRED_ENV_VARS = {
    "GOOGLE_API_KEY": "Google Generative AI API key (required for embeddings and chat)",
}

_missing = [var for var in _REQUIRED_ENV_VARS if not os.getenv(var, "").strip()]
if _missing:
    for var in _missing:
        print(
            f"[FATAL] Missing required environment variable: {var!r} "
            f"— {_REQUIRED_ENV_VARS[var]}",
            file=sys.stderr,
        )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config class (read-only access to all settings)
# ---------------------------------------------------------------------------


class Config:
    # --- Sensitive values loaded from environment only ---
    GOOGLE_API_KEY: str = os.environ["GOOGLE_API_KEY"]

    # --- Application directories ---
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    LOG_DIR: str = os.path.join(DATA_DIR, "logs")

    # --- RAG / chunking parameters ---
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # --- Model identifiers ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "gemini-2.0-flash")


# ---------------------------------------------------------------------------
# Ensure runtime directories exist
# ---------------------------------------------------------------------------

os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.LOG_DIR, exist_ok=True)
