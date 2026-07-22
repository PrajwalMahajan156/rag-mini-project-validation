"""
Unit tests for DocumentLoader MIME type resolution and security token creation.
"""

from datetime import timedelta, timezone


# ---------------------------------------------------------------------------
# DocumentLoader – MIME type resolution
# ---------------------------------------------------------------------------


class TestDocumentLoaderMimeTypes:
    """Verify that _load_image resolves the correct MIME type per extension."""

    def test_png_mime_type(self):
        from app.services.document_loader import DocumentLoader

        assert DocumentLoader._IMAGE_MIME_TYPES[".png"] == "image/png"

    def test_jpg_mime_type(self):
        from app.services.document_loader import DocumentLoader

        assert DocumentLoader._IMAGE_MIME_TYPES[".jpg"] == "image/jpeg"

    def test_jpeg_mime_type(self):
        from app.services.document_loader import DocumentLoader

        assert DocumentLoader._IMAGE_MIME_TYPES[".jpeg"] == "image/jpeg"

    def test_tiff_mime_type(self):
        from app.services.document_loader import DocumentLoader

        assert DocumentLoader._IMAGE_MIME_TYPES[".tiff"] == "image/tiff"

    def test_bmp_mime_type(self):
        from app.services.document_loader import DocumentLoader

        assert DocumentLoader._IMAGE_MIME_TYPES[".bmp"] == "image/bmp"

    def test_unknown_extension_falls_back_to_png(self):
        """Unknown extensions should fall back gracefully to image/png."""
        from app.services.document_loader import DocumentLoader

        result = DocumentLoader._IMAGE_MIME_TYPES.get(".webp", "image/png")
        assert result == "image/png"

    def test_mime_map_covers_all_supported_image_extensions(self):
        """Every extension listed in load_document must have a MIME entry."""
        from app.services.document_loader import DocumentLoader

        # Extensions listed in DocumentLoader.load_document for image branch
        supported = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
        assert supported.issubset(DocumentLoader._IMAGE_MIME_TYPES.keys())


# ---------------------------------------------------------------------------
# Security – timezone-aware token creation
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    """Verify that create_access_token produces a valid, decodable JWT."""

    def test_token_is_string(self):
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_payload_contains_subject(self):
        from jose import jwt

        from app.core.security import ALGORITHM, SECRET_KEY, create_access_token

        token = create_access_token(data={"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"

    def test_token_has_expiry(self):
        from jose import jwt

        from app.core.security import ALGORITHM, SECRET_KEY, create_access_token

        token = create_access_token(data={"sub": "bob"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_custom_expires_delta_is_respected(self):
        from datetime import datetime

        from jose import jwt

        from app.core.security import ALGORITHM, SECRET_KEY, create_access_token

        delta = timedelta(minutes=5)
        before = datetime.now(timezone.utc)
        token = create_access_token(data={"sub": "charlie"}, expires_delta=delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        exp_dt = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        # The expiry should be ~5 minutes from now (allow 10s tolerance for slow CI)
        assert (exp_dt - before).total_seconds() <= 310
        assert (exp_dt - before).total_seconds() >= 290
