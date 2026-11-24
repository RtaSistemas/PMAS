"""API keys for automatic import: management (admin) and use on POST /api/upload-timesheet."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app.deps import get_current_user, get_current_user_allow_change, get_upload_user
from backend.app.main import app
from backend.app.models import ApiKey, AuditLog, Cycle, TimesheetRecord, User
from backend.app.routers.auth import hash_password

CSV = (
    "Colaborador,Data,Horas totais (decimal),Código PEP,PEP\n"
    "Ana Key,2026-01-05,8,KEY-001,Key Project\n"
    "Ana Key,2026-01-06,8,KEY-001,Key Project\n"
).encode("utf-8")


def _user(db, name="svc", role="user", must_change=False) -> User:
    u = User(username=name, hashed_password=hash_password("pass123"), role=role,
             must_change_password=must_change)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture()
def cycle(db_session):
    c = Cycle(name="Jan/2026", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture(autouse=True)
def real_upload_auth(client, db_session):
    """Act as a real administrator row, and use the real upload dependency (it reads X-API-Key).

    The shared `client` fixture has session scope, so this fixture restores the overrides when it ends.
    """
    saved = dict(app.dependency_overrides)
    admin = _user(db_session, "key_admin", role="admin")
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_current_user_allow_change] = lambda: admin
    app.dependency_overrides.pop(get_upload_user, None)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


def _create(client, **body):
    return client.post("/api/api-keys", json={"name": "Importer", **body})


def _upload(client, headers=None):
    return client.post("/api/upload-timesheet", headers=headers or {},
                       files={"file": ("ts.csv", CSV, "text/csv")})


class TestManagement:
    def test_create_returns_the_key_once(self, client):
        r = _create(client)
        assert r.status_code == 201
        body = r.json()
        assert body["key"].startswith("pmas_")
        assert body["key"].startswith(body["key_prefix"])
        listed = client.get("/api/api-keys").json()
        assert len(listed) == 1
        assert "key" not in listed[0]          # the list never shows the key

    def test_database_keeps_a_hash_only(self, client, db_session):
        raw = _create(client).json()["key"]
        stored = db_session.query(ApiKey).one()
        assert raw not in (stored.key_hash, stored.key_prefix, stored.name)
        assert len(stored.key_hash) == 64

    def test_name_is_required(self, client):
        assert client.post("/api/api-keys", json={"name": "ab"}).status_code == 422

    def test_key_can_act_as_another_user(self, client, db_session):
        svc = _user(db_session)
        r = _create(client, user_id=svc.id)
        assert r.status_code == 201
        assert r.json()["username"] == "svc"

    def test_unknown_user_is_rejected(self, client):
        assert _create(client, user_id=99999).status_code == 404

    def test_user_with_temporary_password_is_rejected(self, client, db_session):
        u = _user(db_session, "temp", must_change=True)
        assert _create(client, user_id=u.id).status_code == 400

    def test_revoke_keeps_the_record(self, client):
        key_id = _create(client).json()["id"]
        r = client.delete(f"/api/api-keys/{key_id}")
        assert r.status_code == 200
        assert r.json()["revoked_at"] is not None
        assert client.delete("/api/api-keys/99999").status_code == 404

    def test_create_and_revoke_are_audited(self, client, db_session):
        key_id = _create(client).json()["id"]
        client.delete(f"/api/api-keys/{key_id}")
        actions = {a.action for a in db_session.query(AuditLog).filter_by(entity="api_key")}
        assert actions == {"create", "revoke"}

    def test_regular_user_cannot_manage_keys(self, client, db_session):
        regular = _user(db_session, "plain")
        saved = dict(app.dependency_overrides)
        app.dependency_overrides[get_current_user] = lambda: regular
        app.dependency_overrides[get_current_user_allow_change] = lambda: regular
        try:
            with TestClient(app) as c:
                assert c.get("/api/api-keys").status_code == 403
                assert c.post("/api/api-keys", json={"name": "Importer"}).status_code == 403
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)


class TestUseOnUpload:
    def test_valid_key_imports_the_file(self, client, db_session, cycle):
        raw = _create(client).json()["key"]
        r = _upload(client, {"X-API-Key": raw})
        assert r.status_code == 200, r.text
        assert r.json()["records_inserted"] == 2
        assert db_session.query(TimesheetRecord).count() == 2

    def test_use_updates_last_used_and_writes_an_audit_entry(self, client, db_session, cycle):
        raw = _create(client).json()["key"]
        assert db_session.query(ApiKey).one().last_used_at is None
        _upload(client, {"X-API-Key": raw})
        db_session.expire_all()
        assert db_session.query(ApiKey).one().last_used_at is not None
        assert db_session.query(AuditLog).filter_by(action="upload_api_key").count() == 1

    def test_wrong_key_is_rejected(self, client, cycle):
        r = _upload(client, {"X-API-Key": "pmas_not-a-real-key"})
        assert r.status_code == 401

    def test_revoked_key_is_rejected(self, client, cycle):
        created = _create(client).json()
        client.delete(f"/api/api-keys/{created['id']}")
        assert _upload(client, {"X-API-Key": created["key"]}).status_code == 401

    def test_no_credentials_are_rejected(self, client, cycle):
        assert _upload(client).status_code == 401

    def test_key_does_not_open_other_routes(self, client):
        """The key is valid only on the upload route."""
        raw = _create(client).json()["key"]
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_user_allow_change, None)
        for path in ("/api/api-keys", "/api/cycles", "/api/users", "/api/v2/portfolio"):
            assert client.get(path, headers={"X-API-Key": raw}).status_code == 401, path

    def test_key_applies_the_acl_of_its_user(self, client, db_session, cycle):
        """A key for a regular user with a PEP whitelist cannot import other PEPs."""
        from backend.app.models import Project, UserProjectAccess
        svc = _user(db_session)
        allowed = Project(pep_wbs="OTH-001", name="Other")
        db_session.add(allowed)
        db_session.commit()
        db_session.add(UserProjectAccess(user_id=svc.id, project_id=allowed.id))
        db_session.commit()
        raw = _create(client, user_id=svc.id).json()["key"]
        r = _upload(client, {"X-API-Key": raw})      # the file has PEP KEY-001
        assert r.status_code == 403
        assert "KEY-001" in r.json()["detail"]
        assert db_session.query(TimesheetRecord).count() == 0

    def test_user_that_must_change_the_password_is_blocked(self, client, db_session, cycle):
        svc = _user(db_session)
        raw = _create(client, user_id=svc.id).json()["key"]
        svc.must_change_password = True
        db_session.commit()
        assert _upload(client, {"X-API-Key": raw}).status_code == 403
