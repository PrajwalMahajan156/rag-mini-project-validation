"""
Security unit tests.

Validates that:
- JWT_SECRET must be provided via environment variable
- Known-insecure placeholder values are rejected at startup
- Token creation produces verifiable JWTs with correct expiry
- Password hashing and verification work correctly

All tests that exercise the security module must set JWT_SECRET before
importing it, because the module validates the variable at import time.
"""

import os
import sys
from datetime import timedelta, timezone

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_security(secret: str):
    """Re-import security module with the given JWT_SECRET value."""
    os.environ["JWT_SECRET"] = secret
    # Evict cached module so validation runs fresh on every import
    sys.modules.pop("app.core.security", None)
    import app.core.security as sec

    return sec


def _remove_security_module():
    sys.modules.pop("app.core.security", None)


# ---------------------------------------------------------------------------
# Secret validation at startup
# ---------------------------------------------------------------------------


class TestSecretValidation:
    def teardown_method(self):
        _remove_security_module()
        os.environ.pop("JWT_SECRET", None)

    def test_startup_fails_when_jwt_secret_missing(self):
        """Application must exit(1) if JWT_SECRET is not set."""
        os.environ.pop("JWT_SECRET", None)
        _remove_security_module()
        with pytest.raises(SystemExit) as exc_info:
            import app.core.security  # noqa: F401
        assert exc_info.value.code == 1

    def test_startup_fails_with_known_insecure_placeholder(self):
        """The legacy default 'super-secret-key-for-dev' must be rejected."""
        os.environ["JWT_SECRET"] = "super-secret-key-for-dev"
        _remove_security_module()
        with pytest.raises(SystemExit) as exc_info:
            import app.core.security  # noqa: F401
        assert exc_info.value.code == 1

    def test_startup_fails_with_empty_string(self):
        """An empty JWT_SECRET must be rejected."""
        os.environ["JWT_SECRET"] = ""
        _remove_security_module()
        with pytest.raises(SystemExit) as exc_info:
            import app.core.security  # noqa: F401
        assert exc_info.value.code == 1

    def test_startup_succeeds_with_strong_secret(self):
        """A strong secret must allow the module to import successfully."""
        sec = _import_security("a-very-strong-random-secret-key-1234567890")
        assert sec.SECRET_KEY == "a-very-strong-random-secret-key-1234567890"


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    """Verify create_access_token produces valid, decodable JWTs."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        sec = _import_security("test-secret-key-for-unit-tests-only-xyz")
        self.sec = sec
        yield
        _remove_security_module()
        os.environ.pop("JWT_SECRET", None)

    def test_token_is_non_empty_string(self):
        token = self.sec.create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_payload_contains_subject(self):
        from jose import jwt

        token = self.sec.create_access_token(data={"sub": "alice"})
        payload = jwt.decode(
            token, self.sec.SECRET_KEY, algorithms=[self.sec.ALGORITHM]
        )
        assert payload["sub"] == "alice"

    def test_token_has_expiry_claim(self):
        from jose import jwt

        token = self.sec.create_access_token(data={"sub": "bob"})
        payload = jwt.decode(
            token, self.sec.SECRET_KEY, algorithms=[self.sec.ALGORITHM]
        )
        assert "exp" in payload

    def test_custom_expires_delta_is_respected(self):
        from datetime import datetime

        from jose import jwt

        delta = timedelta(minutes=5)
        before = datetime.now(timezone.utc)
        token = self.sec.create_access_token(
            data={"sub": "charlie"}, expires_delta=delta
        )
        payload = jwt.decode(
            token, self.sec.SECRET_KEY, algorithms=[self.sec.ALGORITHM]
        )
        exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        elapsed = (exp_dt - before).total_seconds()
        assert 290 <= elapsed <= 310  # 5 min ± 10 s tolerance


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# passlib+bcrypt interaction can break on certain environment combinations
# (e.g. bcrypt>=4 changed __about__ attribution). Detect availability early.
_BCRYPT_AVAILABLE = True
try:
    from passlib.context import CryptContext as _TestCtx

    _TestCtx(schemes=["bcrypt"], deprecated="auto").hash("probe")
except Exception:
    _BCRYPT_AVAILABLE = False


@pytest.mark.skipif(
    not _BCRYPT_AVAILABLE,
    reason="bcrypt backend not functional in this environment",
)
class TestPasswordHashing:
    """Verify bcrypt hashing and verification."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        sec = _import_security("test-secret-key-for-unit-tests-only-xyz")
        self.sec = sec
        yield
        _remove_security_module()
        os.environ.pop("JWT_SECRET", None)

    def test_hash_is_not_plaintext(self):
        hashed = self.sec.get_password_hash("mypassword")
        assert hashed != "mypassword"

    def test_verify_password_correct(self):
        hashed = self.sec.get_password_hash("mypassword")
        assert self.sec.verify_password("mypassword", hashed) is True

    def test_verify_password_wrong(self):
        hashed = self.sec.get_password_hash("mypassword")
        assert self.sec.verify_password("wrongpassword", hashed) is False
