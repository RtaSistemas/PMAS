from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.deps import get_current_user
from backend.app.main import app
from backend.app.models import User
from backend.app.routers.auth import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db_session, username: str, password: str, role: str = "user") -> User:
    user = User(username=username, hashed_password=hash_password(password), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Login endpoint
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success_returns_token(self, client, db_session):
        _create_user(db_session, "alice", "secret")
        res = client.post("/api/token", data={"username": "alice", "password": "secret"})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client, db_session):
        _create_user(db_session, "bob", "correct")
        res = client.post("/api/token", data={"username": "bob", "password": "wrong"})
        assert res.status_code == 401

    def test_login_unknown_user_returns_401(self, client):
        res = client.post("/api/token", data={"username": "nobody", "password": "x"})
        assert res.status_code == 401

    def test_login_admin_role_in_token(self, client, db_session):
        import jwt as pyjwt
        from backend.app.deps import SECRET_KEY, ALGORITHM
        _create_user(db_session, "superadmin", "pass", role="admin")
        res = client.post("/api/token", data={"username": "superadmin", "password": "pass"})
        assert res.status_code == 200
        token = res.json()["access_token"]
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "admin"
        assert payload["sub"] == "superadmin"


# ---------------------------------------------------------------------------
# Protected endpoints require valid token
# ---------------------------------------------------------------------------

class TestProtection:
    def test_cycles_without_token_returns_401(self):
        from backend.app.database import get_db
        from sqlalchemy import StaticPool, create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.database import Base

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine)

        def _db():
            db = session_factory()
            try:
                yield db
            finally:
                db.close()

        saved = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = _db
        try:
            with TestClient(app, raise_server_exceptions=True) as c:
                res = c.get("/api/cycles")
            assert res.status_code == 401
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Token validation with the real dependency (T1: PyJWT)
# ---------------------------------------------------------------------------

import base64
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt as pyjwt_lib

from backend.app.deps import ALGORITHM, SECRET_KEY, get_current_user_allow_change

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def real_auth(client):
    """Use the real token check on /api/users/me (the shared client mocks it)."""
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_allow_change, None)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _payload(username: str, hours: float = 1.0) -> dict:
    return {"sub": username, "role": "user", "exp": datetime.now(timezone.utc) + timedelta(hours=hours)}


class TestTokenValidation:
    def test_valid_token_is_accepted(self, real_auth, db_session):
        _create_user(db_session, "tok_ok", "pass123")
        token = pyjwt_lib.encode(_payload("tok_ok"), SECRET_KEY, algorithm=ALGORITHM)
        assert real_auth.get("/api/users/me", headers=_bearer(token)).status_code == 200

    def test_expired_token_returns_401(self, real_auth, db_session):
        _create_user(db_session, "tok_old", "pass123")
        token = pyjwt_lib.encode(_payload("tok_old", hours=-1), SECRET_KEY, algorithm=ALGORITHM)
        assert real_auth.get("/api/users/me", headers=_bearer(token)).status_code == 401

    def test_token_signed_with_another_key_returns_401(self, real_auth, db_session):
        _create_user(db_session, "tok_key", "pass123")
        token = pyjwt_lib.encode(_payload("tok_key"), "another-key-" + "x" * 40, algorithm=ALGORITHM)
        assert real_auth.get("/api/users/me", headers=_bearer(token)).status_code == 401

    def test_token_with_alg_none_returns_401(self, real_auth, db_session):
        _create_user(db_session, "tok_none", "pass123")

        def b64(data: dict) -> str:
            return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

        exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        token = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({'sub': 'tok_none', 'role': 'admin', 'exp': exp})}."
        assert real_auth.get("/api/users/me", headers=_bearer(token)).status_code == 401

    def test_token_for_a_deleted_user_returns_401(self, real_auth):
        token = pyjwt_lib.encode(_payload("nobody_here"), SECRET_KEY, algorithm=ALGORITHM)
        assert real_auth.get("/api/users/me", headers=_bearer(token)).status_code == 401

    def test_garbage_token_returns_401(self, real_auth):
        assert real_auth.get("/api/users/me", headers=_bearer("not.a.token")).status_code == 401


class TestNoJoseDependency:
    """python-jose pulls ecdsa (timing-attack CVE with no upstream fix)."""

    def test_requirements_do_not_name_python_jose(self):
        for name in ("requirements.txt", "requirements-lock.txt"):
            text = (ROOT / name).read_text(encoding="utf-8").lower()
            assert "jose" not in text, name

    def test_backend_does_not_import_jose(self):
        offenders = [
            str(p.relative_to(ROOT)) for p in (ROOT / "backend").rglob("*.py")
            if re.search(r"^\s*(from|import)\s+jose\b", p.read_text(encoding="utf-8"), re.M)
        ]
        assert offenders == []
