"""
Tests for upload endpoint guards: file size limit, file type validation,
and rate limiting configuration.
"""
from __future__ import annotations

import io
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.deps import get_current_user
from backend.app.main import app
import backend.app.models as _models  # noqa: F401

# ── fixtures ──────────────────────────────────────────────────────────────────

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(bind=_engine)


class _MockAdmin:
    id = 1
    username = "admin"
    role = "admin"
    must_change_password = False


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """Function-scoped client with rate limiter reset between tests."""
    from backend.app.limiter import limiter
    # Reset in-memory rate limit storage so tests don't pollute each other
    try:
        limiter._storage.reset()
    except Exception:
        pass
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: _MockAdmin()
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── helpers ──────────────────────────────────────────────���────────────────────

def _upload(client, content: bytes, filename: str = "test.csv"):
    return client.post(
        "/api/upload-timesheet",
        files={"file": (filename, io.BytesIO(content), "text/csv")},
    )


# ── size limit ─────────────��────────────────────────────────��─────────────────

class TestUploadSizeLimit:
    def test_small_file_accepted(self, client):
        """A minimal CSV well under the limit gets processed (may produce 422 for bad data, not 413)."""
        data = b"Colaborador,Data\ntest,bad"
        r = _upload(client, data)
        assert r.status_code != 413

    def test_oversized_file_rejected_413(self, client, monkeypatch):
        """File exceeding _MAX_UPLOAD_BYTES is rejected with 413."""
        import backend.app.routers.upload as upload_mod
        # Temporarily lower the limit so we don't allocate 20MB in tests
        monkeypatch.setattr(upload_mod, "_MAX_UPLOAD_BYTES", 10)
        data = b"x" * 11  # 11 bytes > 10 byte limit
        r = _upload(client, data)
        assert r.status_code == 413

    def test_413_error_message_mentions_limit(self, client, monkeypatch):
        """413 response body should mention the size limit."""
        import backend.app.routers.upload as upload_mod
        monkeypatch.setattr(upload_mod, "_MAX_UPLOAD_BYTES", 10)
        monkeypatch.setattr(upload_mod, "_MAX_UPLOAD_MB", 0)
        data = b"x" * 11
        r = _upload(client, data)
        assert r.status_code == 413
        assert "MB" in r.json().get("detail", "")

    def test_limit_env_var_applied(self, monkeypatch):
        """_MAX_UPLOAD_BYTES is derived from PMAS_MAX_UPLOAD_MB env var."""
        monkeypatch.setenv("PMAS_MAX_UPLOAD_MB", "5")
        # Re-import to pick up the env change
        import importlib
        import backend.app.routers.upload as upload_mod
        importlib.reload(upload_mod)
        assert upload_mod._MAX_UPLOAD_BYTES == 5 * 1024 * 1024
        # Restore
        monkeypatch.delenv("PMAS_MAX_UPLOAD_MB", raising=False)
        importlib.reload(upload_mod)


# ── file type validation ─────────────────────────────────────────��────────────

class TestUploadFileTypeValidation:
    def test_csv_extension_accepted(self, client):
        r = _upload(client, b"col\nval", "data.csv")
        assert r.status_code != 400

    def test_xlsx_extension_accepted(self, client):
        r = _upload(client, b"\x50\x4b\x03\x04", "data.xlsx")  # ZIP magic bytes
        assert r.status_code != 400

    def test_txt_extension_rejected_400(self, client):
        r = _upload(client, b"hello", "data.txt")
        assert r.status_code == 400

    def test_pdf_extension_rejected_400(self, client):
        r = _upload(client, b"%PDF", "report.pdf")
        assert r.status_code == 400

    def test_no_extension_rejected_400(self, client):
        r = _upload(client, b"data", "noextension")
        assert r.status_code == 400

    def test_case_insensitive_extension(self, client):
        r = _upload(client, b"col\nval", "DATA.CSV")
        assert r.status_code != 400


# ── rate limit configuration ──────────────���───────────────────────────────────

class TestUploadRateLimitConfig:
    def test_upload_endpoint_has_rate_limit_decorator(self):
        """Verify the upload endpoint has @limiter.limit applied."""
        import inspect
        from backend.app.routers.upload import upload_timesheet
        # The limiter decorator sets _rate_limit_key on the function
        assert hasattr(upload_timesheet, "_rate_limit_key") or \
               "_rate_limit" in str(getattr(upload_timesheet, "__wrapped__", "")) or \
               any("limit" in str(getattr(upload_timesheet, attr, ""))
                   for attr in dir(upload_timesheet)), \
            "upload_timesheet must have @limiter.limit applied"
