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
        from jose import jwt as pyjwt
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
