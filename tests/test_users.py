from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from backend.app.deps import get_current_user
from backend.app.main import app
from backend.app.models import User
from backend.app.routers.auth import hash_password


def _make_user(db_session, username: str, password: str = "pass123", role: str = "user") -> User:
    u = User(username=username, hashed_password=hash_password(password), role=role)
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@contextmanager
def _acting_as(user: User):
    """Temporarily impersonate *user* for one TestClient block."""
    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# GET /api/users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_empty(self, client):
        assert client.get("/api/users").json() == []

    def test_returns_created_user(self, client, db_session):
        _make_user(db_session, "alice")
        names = [u["username"] for u in client.get("/api/users").json()]
        assert "alice" in names

    def test_hashed_password_not_exposed(self, client, db_session):
        _make_user(db_session, "bob")
        data = client.get("/api/users").json()
        assert all("hashed_password" not in u for u in data)

    def test_non_admin_forbidden(self, db_session):
        regular = _make_user(db_session, "carol")
        with _acting_as(regular) as c:
            assert c.get("/api/users").status_code == 403


# ---------------------------------------------------------------------------
# POST /api/users
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_success(self, client):
        r = client.post("/api/users", json={"username": "dave", "password": "pass123"})
        assert r.status_code == 201
        d = r.json()
        assert d["username"] == "dave"
        assert d["role"] == "user"
        assert "hashed_password" not in d

    def test_default_role_is_user(self, client):
        r = client.post("/api/users", json={"username": "eve", "password": "pass123"})
        assert r.json()["role"] == "user"

    def test_can_create_admin(self, client):
        r = client.post("/api/users", json={"username": "frank", "password": "pass123", "role": "admin"})
        assert r.status_code == 201
        assert r.json()["role"] == "admin"

    def test_duplicate_username_rejected(self, client, db_session):
        _make_user(db_session, "grace")
        r = client.post("/api/users", json={"username": "grace", "password": "pass123"})
        assert r.status_code == 400

    def test_short_username_rejected(self, client):
        r = client.post("/api/users", json={"username": "ab", "password": "pass123"})
        assert r.status_code == 422

    def test_short_password_rejected(self, client):
        r = client.post("/api/users", json={"username": "henry", "password": "12345"})
        assert r.status_code == 422

    def test_non_admin_forbidden(self, db_session):
        regular = _make_user(db_session, "iris")
        with _acting_as(regular) as c:
            r = c.post("/api/users", json={"username": "newguy", "password": "pass123"})
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/users/{id}/password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_admin_changes_any_password_without_current(self, client, db_session):
        target = _make_user(db_session, "jack", "oldpass")
        r = client.patch(f"/api/users/{target.id}/password", json={"new_password": "newpass123"})
        assert r.status_code == 200

    def test_user_changes_own_password_with_correct_current(self, db_session):
        regular = _make_user(db_session, "karen", "oldpass")
        with _acting_as(regular) as c:
            r = c.patch(f"/api/users/{regular.id}/password",
                        json={"new_password": "newpass123", "current_password": "oldpass"})
        assert r.status_code == 200

    def test_user_wrong_current_password_rejected(self, db_session):
        regular = _make_user(db_session, "leo", "oldpass")
        with _acting_as(regular) as c:
            r = c.patch(f"/api/users/{regular.id}/password",
                        json={"new_password": "newpass123", "current_password": "wrong"})
        assert r.status_code == 400

    def test_user_missing_current_password_rejected(self, db_session):
        regular = _make_user(db_session, "mia", "oldpass")
        with _acting_as(regular) as c:
            r = c.patch(f"/api/users/{regular.id}/password",
                        json={"new_password": "newpass123"})
        assert r.status_code == 422

    def test_user_cannot_change_others_password(self, db_session):
        regular = _make_user(db_session, "ned", "pass")
        other   = _make_user(db_session, "ola", "pass")
        with _acting_as(regular) as c:
            r = c.patch(f"/api/users/{other.id}/password",
                        json={"new_password": "newpass123", "current_password": "pass"})
        assert r.status_code == 403

    def test_not_found(self, client):
        r = client.patch("/api/users/99999/password", json={"new_password": "newpass123"})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/users/{id}
# ---------------------------------------------------------------------------

class TestDeleteUser:
    def test_success(self, client, db_session):
        u = _make_user(db_session, "pete")
        assert client.delete(f"/api/users/{u.id}").status_code == 204

    def test_not_found(self, client):
        assert client.delete("/api/users/99999").status_code == 404

    def test_deleted_not_in_list(self, client, db_session):
        u = _make_user(db_session, "quinn")
        client.delete(f"/api/users/{u.id}")
        names = [x["username"] for x in client.get("/api/users").json()]
        assert "quinn" not in names

    def test_cannot_delete_self(self, db_session):
        admin = _make_user(db_session, "selfdelete", role="admin")
        with _acting_as(admin) as c:
            r = c.delete(f"/api/users/{admin.id}")
        assert r.status_code == 409

    def test_non_admin_forbidden(self, db_session):
        regular = _make_user(db_session, "rosa")
        victim  = _make_user(db_session, "sam")
        with _acting_as(regular) as c:
            r = c.delete(f"/api/users/{victim.id}")
        assert r.status_code == 403
