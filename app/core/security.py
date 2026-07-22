"""
Security utilities: password hashing and JWT token creation/verification.

JWT_SECRET *must* be provided via the environment (or .env file). The
application will refuse to start if the variable is absent or contains the
known-insecure placeholder value used in older development builds.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ---------------------------------------------------------------------------
# Secret key validation – fail fast rather than silently use a weak key
# ---------------------------------------------------------------------------

_INSECURE_PLACEHOLDERS = {
    "super-secret-key-for-dev",
    "changeme",
    "secret",
    "jwt-secret",
    "",
}

_raw_secret = os.getenv("JWT_SECRET", "")

if not _raw_secret or _raw_secret.strip() in _INSECURE_PLACEHOLDERS:
    print(
        "[FATAL] JWT_SECRET environment variable is missing or set to an insecure "
        "placeholder. Set a strong, random value in your .env file or deployment "
        "secrets manager before starting the application.",
        file=sys.stderr,
    )
    sys.exit(1)

SECRET_KEY: str = _raw_secret

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash of password."""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload claims to embed in the token.
        expires_delta: Optional custom expiry duration.  Defaults to
            ACCESS_TOKEN_EXPIRE_MINUTES (24 h).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    delta = (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire = datetime.now(timezone.utc) + delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
