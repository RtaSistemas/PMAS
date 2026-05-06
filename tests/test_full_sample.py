"""
Full end-to-end sample that imports and exercises every API function in PMAS.

Run with:
    pytest tests/test_full_sample.py -v

Uses the same in-memory SQLite engine wired in conftest.py — no pmas.db touched.
Each test class is self-contained: setUp helpers create exactly what is needed,
clean_db fixture (autouse in conftest) wipes state between tests.
"""
from __future__ import annotations

import calendar
import io
from contextlib import contextmanager
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app.deps import get_current_user
from backend.app.main import app
from backend.app.models import (
    Collaborator,
    Cycle,
    GlobalConfig,
    Project,
    ProjectCyclePlan,
    RateCard,
    SeniorityLevel,
    TimesheetRecord,
    User,
)
from backend.app.routers.auth import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_day(y: int, m: int) -> int:
    return calendar.monthrange(y, m)[1]


def _mk_cycle(db, name, y, m, quarantine=False, is_active=True):
    c = Cycle(
        name=name,
        start_date=date(y, m, 1),
        end_date=date(y, m, _last_day(y, m)),
        is_quarantine=quarantine,
        is_active=is_active,
    )
    db.add(c); db.commit(); db.refresh(c)
    return c


def _mk_user(db, username, password="pass1234", role="user"):
    u = User(username=username, hashed_password=hash_password(password), role=role)
    db.add(u); db.commit(); db.refresh(u)
    return u


def _mk_level(db, name):
    sl = SeniorityLevel(name=name)
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


def _mk_rate(db, level, hourly_rate, valid_from, valid_to=None):
    rc = RateCard(
        seniority_level_id=level.id,
        hourly_rate=hourly_rate,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    db.add(rc); db.commit(); db.refresh(rc)
    return rc


def _mk_collab(db, name, seniority_level=None):
    c = Collaborator(
        name=name,
        seniority_level_id=seniority_level.id if seniority_level else None,
    )
    db.add(c); db.commit(); db.refresh(c)
    return c


def _mk_project(db, pep, name="Proj", budget_h=None, budget_cost=None, status="ativo"):
    p = Project(
        pep_wbs=pep,
        name=name,
        budget_hours=budget_h,
        budget_cost=budget_cost,
        status=status,
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def _mk_record(db, cycle, collab, pep, desc="D", normal=8.0, extra=0.0, standby=0.0,
               day=10, cost_per_hour=0.0):
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep,
        pep_description=desc,
        normal_hours=normal,
        extra_hours=extra,
        standby_hours=standby,
        cost_per_hour=cost_per_hour,
    )
    db.add(r); db.commit()
    return r


def _csv(rows: list[tuple]) -> bytes:
    """Build a minimal CSV from (name, date_str, hours[, extra[, standby[, pep[, pep_desc]]]]) tuples."""
    header = "Colaborador,Data,Horas totais (decimal),Hora extra,Hora sobreaviso,Código PEP,PEP"
    lines = [header]
    for row in rows:
        name, dt, h = row[0], row[1], row[2]
        extra   = row[3] if len(row) > 3 else 0
        standby = row[4] if len(row) > 4 else 0
        pep     = row[5] if len(row) > 5 else ""
        pep_d   = row[6] if len(row) > 6 else ""
        lines.append(f"{name},{dt},{h},{extra},{standby},{pep},{pep_d}")
    return "\n".join(lines).encode()


@contextmanager
def _acting_as(user):
    """Temporarily override the current-user dependency for one TestClient block.

    Uses try/finally to guarantee override restoration even when assertions
    inside the with-block raise AssertionError.
    """
    saved = dict(app.dependency_overrides)
    try:
        app.dependency_overrides[get_current_user] = lambda: user
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


# ===========================================================================
# 1. AUTH — POST /api/token
# ===========================================================================

class TestAuth:
    def test_login_success(self, client, db_session):
        _mk_user(db_session, "auth_alice", "secret123")
        r = client.post("/api/token", data={"username": "auth_alice", "password": "secret123"})
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    def test_wrong_password(self, client, db_session):
        _mk_user(db_session, "auth_bob", "correct")
        assert client.post("/api/token", data={"username": "auth_bob", "password": "bad"}).status_code == 401

    def test_unknown_user(self, client):
        assert client.post("/api/token", data={"username": "nobody", "password": "x"}).status_code == 401

    def test_admin_role_encoded_in_token(self, client, db_session):
        from jose import jwt as pyjwt
        from backend.app.deps import SECRET_KEY, ALGORITHM
        _mk_user(db_session, "jwt_admin", "pass1234", role="admin")
        r = client.post("/api/token", data={"username": "jwt_admin", "password": "pass1234"})
        payload = pyjwt.decode(r.json()["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["role"] == "admin"
        assert payload["sub"] == "jwt_admin"

    def test_no_token_returns_401(self):
        """Endpoint without dependency override should reject unauthenticated requests."""
        from backend.app.database import Base, get_db
        from sqlalchemy import StaticPool, create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        sf = sessionmaker(bind=engine)
        def _db():
            db = sf(); yield db; db.close()
        saved = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = _db
        try:
            with TestClient(app, raise_server_exceptions=True) as c:
                assert c.get("/api/cycles").status_code == 401
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)


# ===========================================================================
# 2. USERS — /api/users
# ===========================================================================

class TestUsers:
    def test_list_empty(self, client):
        assert client.get("/api/users").json() == []

    def test_create_user(self, client):
        r = client.post("/api/users", json={"username": "newuser", "password": "pass1234"})
        assert r.status_code == 201
        assert r.json()["role"] == "user"
        assert "hashed_password" not in r.json()

    def test_create_admin(self, client):
        r = client.post("/api/users", json={"username": "myadmin", "password": "pass1234", "role": "admin"})
        assert r.status_code == 201
        assert r.json()["role"] == "admin"

    def test_duplicate_username_rejected(self, client, db_session):
        _mk_user(db_session, "dup_user")
        assert client.post("/api/users", json={"username": "dup_user", "password": "pass1234"}).status_code == 400

    def test_short_username_rejected(self, client):
        assert client.post("/api/users", json={"username": "ab", "password": "pass1234"}).status_code == 422

    def test_short_password_rejected(self, client):
        assert client.post("/api/users", json={"username": "longname", "password": "123"}).status_code == 422

    def test_change_password_admin(self, client, db_session):
        u = _mk_user(db_session, "pwd_user", "oldpass")
        r = client.patch(f"/api/users/{u.id}/password", json={"new_password": "newpass1234"})
        assert r.status_code == 200

    def test_change_password_self(self, db_session):
        u = _mk_user(db_session, "self_user", "oldpass")
        with _acting_as(u) as c:
            r = c.patch(f"/api/users/{u.id}/password",
                        json={"new_password": "newpass1234", "current_password": "oldpass"})
        assert r.status_code == 200

    def test_change_password_wrong_current(self, db_session):
        u = _mk_user(db_session, "wrong_pwd", "oldpass")
        with _acting_as(u) as c:
            r = c.patch(f"/api/users/{u.id}/password",
                        json={"new_password": "newpass1234", "current_password": "bad"})
        assert r.status_code == 400

    def test_non_admin_cannot_list(self, db_session):
        u = _mk_user(db_session, "nonadmin_list")
        with _acting_as(u) as c:
            r = c.get("/api/users")
        assert r.status_code == 403

    def test_delete_user(self, client, db_session):
        u = _mk_user(db_session, "del_me")
        assert client.delete(f"/api/users/{u.id}").status_code == 204
        names = [x["username"] for x in client.get("/api/users").json()]
        assert "del_me" not in names

    def test_cannot_delete_self(self, db_session):
        admin = _mk_user(db_session, "selfdelete", role="admin")
        with _acting_as(admin) as c:
            r = c.delete(f"/api/users/{admin.id}")
        assert r.status_code == 409

    def test_delete_not_found(self, client):
        assert client.delete("/api/users/99999").status_code == 404

    def test_non_admin_cannot_delete_others(self, client, db_session):
        regular = _mk_user(db_session, "delnonadmin")
        victim = _mk_user(db_session, "victim_usr")
        with _acting_as(regular) as c:
            r = c.delete(f"/api/users/{victim.id}")
        assert r.status_code == 403


# ===========================================================================
# 3. CYCLES — /api/cycles
# ===========================================================================

class TestCycles:
    def test_list_empty(self, client):
        assert client.get("/api/cycles").json() == []

    def test_create_cycle(self, client):
        r = client.post("/api/cycles", json={
            "name": "Jan/2026",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["name"] == "Jan/2026"
        assert d["is_quarantine"] is False
        assert d["is_active"] is True

    def test_date_range_validation(self, client):
        r = client.post("/api/cycles", json={
            "name": "Bad",
            "start_date": "2026-03-01",
            "end_date": "2026-01-01",
        })
        assert r.status_code == 422

    def test_update_cycle(self, client, db_session):
        cy = _mk_cycle(db_session, "Old", 2026, 1)
        r = client.put(f"/api/cycles/{cy.id}", json={
            "name": "New",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_update_not_found(self, client):
        assert client.put("/api/cycles/99999", json={
            "name": "X", "start_date": "2026-01-01", "end_date": "2026-01-31"
        }).status_code == 404

    def test_toggle_lock(self, client, db_session):
        """toggle-status flips is_closed (not is_quarantine). Requires admin."""
        cy = _mk_cycle(db_session, "Lockable", 2026, 2)
        r = client.patch(f"/api/cycles/{cy.id}/toggle-status")
        assert r.status_code == 200
        assert r.json()["is_closed"] is True
        r2 = client.patch(f"/api/cycles/{cy.id}/toggle-status")
        assert r2.json()["is_closed"] is False

    def test_toggle_archive(self, client, db_session):
        cy = _mk_cycle(db_session, "Archivable", 2026, 3)
        r = client.patch(f"/api/cycles/{cy.id}/toggle-archive")
        assert r.status_code == 200
        assert r.json()["is_active"] is False
        r2 = client.patch(f"/api/cycles/{cy.id}/toggle-archive")
        assert r2.json()["is_active"] is True

    def test_archived_hidden_by_default(self, client):
        client.post("/api/cycles", json={"name": "Visible", "start_date": "2026-01-01", "end_date": "2026-01-31"})
        arch = client.post("/api/cycles", json={"name": "Archived", "start_date": "2026-02-01", "end_date": "2026-02-28"}).json()
        client.patch(f"/api/cycles/{arch['id']}/toggle-archive")
        names = [c["name"] for c in client.get("/api/cycles").json()]
        assert "Visible" in names
        assert "Archived" not in names

    def test_archived_visible_when_requested(self, client):
        client.post("/api/cycles", json={"name": "Active", "start_date": "2026-01-01", "end_date": "2026-01-31"})
        arch = client.post("/api/cycles", json={"name": "Gone", "start_date": "2026-02-01", "end_date": "2026-02-28"}).json()
        client.patch(f"/api/cycles/{arch['id']}/toggle-archive")
        names = [c["name"] for c in client.get("/api/cycles?include_archived=true").json()]
        assert "Active" in names and "Gone" in names

    def test_import_cycles_csv(self, client):
        # Router expects lowercase: name, start_date, end_date
        csv_data = "name,start_date,end_date\nFev/2026,2026-02-01,2026-02-28\n"
        r = client.post("/api/cycles/import",
                        files={"file": ("cycles.csv", csv_data.encode(), "text/csv")})
        assert r.status_code == 200
        assert r.json()["created"] >= 1

    def test_delete_cycle(self, client):
        cy = client.post("/api/cycles", json={"name": "ToDelete", "start_date": "2026-04-01", "end_date": "2026-04-30"}).json()
        assert client.delete(f"/api/cycles/{cy['id']}").status_code == 204
        assert all(c["name"] != "ToDelete" for c in client.get("/api/cycles").json())

    def test_delete_with_records_rejected(self, client, db_session):
        cy = _mk_cycle(db_session, "HasRecords", 2026, 5)
        co = _mk_collab(db_session, "linked_collab")
        _mk_record(db_session, cy, co, "PEP-DEL")
        assert client.delete(f"/api/cycles/{cy.id}").status_code == 409

    def test_non_admin_cannot_toggle_archive(self, db_session):
        """toggle-archive is AdminUser — regular users get 403."""
        cy = _mk_cycle(db_session, "Protected", 2026, 6)
        u = _mk_user(db_session, "nonadmin_cy")
        with _acting_as(u) as c:
            r = c.patch(f"/api/cycles/{cy.id}/toggle-archive")
        assert r.status_code == 403


# ===========================================================================
# 4. PROJECTS — /api/projects
# ===========================================================================

class TestProjects:
    def test_list_empty(self, client):
        assert client.get("/api/projects").json() == []

    def test_create_project(self, client):
        r = client.post("/api/projects", json={
            "pep_wbs": "60OP-001",
            "name": "Infra",
            "status": "ativo",
            "budget_hours": 200.0,
            "budget_cost": 40000.0,
        })
        assert r.status_code == 201
        d = r.json()
        assert d["pep_wbs"] == "60OP-001"
        assert d["budget_hours"] == 200.0
        assert d["budget_cost"] == 40000.0

    def test_duplicate_pep_rejected(self, client, db_session):
        _mk_project(db_session, "DUP-001")
        r = client.post("/api/projects", json={"pep_wbs": "DUP-001", "name": "Dup", "status": "ativo"})
        assert r.status_code == 409

    def test_update_project(self, client, db_session):
        p = _mk_project(db_session, "UPD-001", name="Old")
        r = client.put(f"/api/projects/{p.id}", json={
            "pep_wbs": "UPD-001",
            "name": "New",
            "status": "ativo",
            "budget_hours": 100.0,
        })
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_import_projects_csv(self, client):
        # Router expects lowercase column: pep_wbs
        csv_data = "pep_wbs,name,client,manager,status\nIMP-001,ImpProj,Client,Mgr,ativo\n"
        r = client.post("/api/projects/import",
                        files={"file": ("projects.csv", csv_data.encode(), "text/csv")})
        assert r.status_code == 200
        assert r.json()["created"] >= 1

    def test_delete_project(self, client):
        p = client.post("/api/projects", json={"pep_wbs": "DEL-001", "name": "DelProj", "status": "ativo"}).json()
        assert client.delete(f"/api/projects/{p['id']}").status_code == 204
        assert all(x["pep_wbs"] != "DEL-001" for x in client.get("/api/projects").json())

    def test_delete_not_found(self, client):
        assert client.delete("/api/projects/99999").status_code == 404


# ===========================================================================
# 5. UPLOAD TIMESHEET — POST /api/upload-timesheet
# ===========================================================================

class TestUploadTimesheet:
    def test_csv_upload_creates_records(self, client, db_session):
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        data = _csv([("Ana Costa", "15/01/2026", 8.0)])
        r = client.post("/api/upload-timesheet",
                        files={"file": ("sheet.csv", data, "text/csv")})
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["records_inserted"] >= 1

    def test_xlsx_upload(self, client, db_session):
        import openpyxl
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Colaborador", "Data", "Horas totais (decimal)"])
        ws.append(["Carlos Lima", "15/01/2026", 6.0])
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        r = client.post("/api/upload-timesheet",
                        files={"file": ("sheet.xlsx", buf.read(),
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert r.status_code == 200
        assert r.json()["records_inserted"] >= 1

    def test_invalid_extension_rejected(self, client):
        r = client.post("/api/upload-timesheet",
                        files={"file": ("sheet.txt", b"data", "text/plain")})
        assert r.status_code == 400

    def test_intra_batch_deduplication(self, client, db_session):
        """Intra-batch dedup: identical rows in one CSV produce only one record."""
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        # Two identical rows in the same upload
        data = _csv([
            ("Dup User", "10/01/2026", 8.0),
            ("Dup User", "10/01/2026", 8.0),
        ])
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.json()["records_inserted"] == 1
        assert r.json()["records_skipped"] >= 1

    def test_quarantine_created_for_out_of_range_date(self, client, db_session):
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        data = _csv([("Out Of Range", "01/06/2025", 4.0)])  # no cycle covers June 2025
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.status_code == 200
        cycles = client.get("/api/cycles?include_archived=true").json()
        assert any(c["is_quarantine"] for c in cycles)

    def test_weekend_anomaly_warning(self, client, db_session):
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        # 2026-01-10 is Saturday
        data = _csv([("Weekend Worker", "10/01/2026", 8.0)])
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.status_code == 200
        warnings = r.json().get("warnings", [])
        assert any("fim de semana" in w.lower() or "weekend" in w.lower() for w in warnings)

    def test_cost_frozen_at_ingestion(self, client, db_session):
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        sl = _mk_level(db_session, "Sênior")
        _mk_rate(db_session, sl, 150.0, date(2026, 1, 1))
        _mk_collab(db_session, "Frozen Collab", seniority_level=sl)
        data = _csv([("Frozen Collab", "15/01/2026", 8.0)])
        client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        rec = db_session.query(TimesheetRecord).first()
        assert rec.cost_per_hour == 150.0
        # Change the rate — stored cost_per_hour must not change (EVM freeze pattern)
        rc = db_session.query(RateCard).first()
        rc.hourly_rate = 999.0
        db_session.commit()
        db_session.refresh(rec)
        assert rec.cost_per_hour == 150.0


# ===========================================================================
# 6. DASHBOARD — /api/dashboard  &  /api/dashboard/{cycle_id}
# ===========================================================================

class TestDashboard:
    def _seed(self, db):
        cy = _mk_cycle(db, "Jan/2026", 2026, 1)
        co = _mk_collab(db, "dash_collab")
        _mk_record(db, cy, co, "PEP-DASH", normal=40.0, extra=8.0, day=5)
        return cy, co

    def test_dashboard_all_cycles(self, client, db_session):
        self._seed(db_session)
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        # DashboardOut.data contains CollaboratorHours rows
        names = [x["collaborator"] for x in r.json()["data"]]
        assert "dash_collab" in names

    def test_dashboard_by_cycle(self, client, db_session):
        cy, _ = self._seed(db_session)
        r = client.get(f"/api/dashboard/{cy.id}")
        assert r.status_code == 200
        rows = r.json()["data"]
        assert any(x["collaborator"] == "dash_collab" for x in rows)

    def test_dashboard_date_filter(self, client, db_session):
        self._seed(db_session)
        r = client.get("/api/dashboard?date_from=2026-01-01&date_to=2026-01-31")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1

    def test_dashboard_cycle_not_found(self, client):
        assert client.get("/api/dashboard/99999").status_code == 404

    def test_pep_radar(self, client, db_session):
        # Router prefix is /api/dashboard → full path is /api/dashboard/pep-radar
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        co = _mk_collab(db_session, "radar_collab")
        _mk_record(db_session, cy, co, "RAD-001", desc="Radar PEP", normal=16.0)
        r = client.get("/api/dashboard/pep-radar")
        assert r.status_code == 200
        assert any(x["pep_description"] == "Radar PEP" for x in r.json())

    def test_collaborator_timeline(self, client, db_session):
        """Timeline endpoint lives under /api/dashboard/collaborator-timeline."""
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        co = _mk_collab(db_session, "timeline_collab")
        _mk_record(db_session, cy, co, "TL-001", normal=24.0)
        r = client.get("/api/dashboard/collaborator-timeline?collaborator_name=timeline_collab")
        assert r.status_code == 200
        assert len(r.json()) >= 1
        assert r.json()[0]["normal_hours"] == 24.0


# ===========================================================================
# 7. REFERENCE — /api/collaborators  &  /api/peps
# ===========================================================================

class TestReference:
    def test_collaborators_empty(self, client):
        assert client.get("/api/collaborators").json() == []

    def test_collaborators_after_upload(self, client, db_session):
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        data = _csv([("Ref Collab", "15/01/2026", 8.0, 0, 0, "REF-001", "Ref PEP")])
        client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        names = [x["name"] for x in client.get("/api/collaborators").json()]
        assert "Ref Collab" in names

    def test_peps_empty(self, client):
        assert client.get("/api/peps").json() == []

    def test_peps_after_upload(self, client, db_session):
        # PepOut has field "code", not "pep_wbs"
        _mk_cycle(db_session, "Jan/2026", 2026, 1)
        data = _csv([("PEP User", "15/01/2026", 8.0, 0, 0, "REF-002", "My PEP")])
        client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        peps = client.get("/api/peps").json()
        assert any(p["code"] == "REF-002" for p in peps)

    def test_collaborators_filter_by_cycle(self, client, db_session):
        cy1 = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        cy2 = _mk_cycle(db_session, "Feb/2026", 2026, 2)
        data1 = _csv([("Cy1 Only", "15/01/2026", 8.0)])
        data2 = _csv([("Cy2 Only", "15/02/2026", 8.0)])
        client.post("/api/upload-timesheet", files={"file": ("a.csv", data1, "text/csv")})
        client.post("/api/upload-timesheet", files={"file": ("b.csv", data2, "text/csv")})
        names_cy1 = [x["name"] for x in client.get(f"/api/collaborators?cycle_id={cy1.id}").json()]
        assert "Cy1 Only" in names_cy1
        assert "Cy2 Only" not in names_cy1


# ===========================================================================
# 8. ANALYTICS — portfolio-health, trends, allocation, forecast
# ===========================================================================

class TestAnalytics:
    def _seed_evm(self, db):
        cy1 = _mk_cycle(db, "Jan/2026", 2026, 1)
        cy2 = _mk_cycle(db, "Feb/2026", 2026, 2)
        proj = _mk_project(db, "EVM-001", budget_h=100.0, budget_cost=20000.0)
        co   = _mk_collab(db, "evm_collab")
        _mk_record(db, cy1, co, "EVM-001", desc="EVM Proj", normal=40.0, cost_per_hour=100.0)
        _mk_record(db, cy2, co, "EVM-001", desc="EVM Proj", normal=30.0, cost_per_hour=100.0)
        return proj, cy1, cy2

    # -- portfolio-health
    def test_portfolio_health_empty(self, client):
        assert client.get("/api/portfolio-health").json() == []

    def test_portfolio_health_hours(self, client, db_session):
        self._seed_evm(db_session)
        result = client.get("/api/portfolio-health").json()
        item = next(x for x in result if x["pep_wbs"] == "EVM-001")
        assert item["consumed_hours"] == 70.0
        assert item["budget_hours"] == 100.0

    def test_portfolio_health_actual_cost(self, client, db_session):
        self._seed_evm(db_session)
        result = client.get("/api/portfolio-health").json()
        item = next(x for x in result if x["pep_wbs"] == "EVM-001")
        assert item["actual_cost"] == pytest.approx(7000.0)

    def test_portfolio_health_date_filter(self, client, db_session):
        self._seed_evm(db_session)
        r = client.get("/api/portfolio-health?date_from=2026-01-01&date_to=2026-01-31")
        item = next(x for x in r.json() if x["pep_wbs"] == "EVM-001")
        assert item["consumed_hours"] == 40.0  # only Jan

    def test_portfolio_health_pep_filter(self, client, db_session):
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        co = _mk_collab(db_session, "pep_filter_co")
        _mk_record(db_session, cy, co, "ALPHA-001", normal=10.0)
        _mk_record(db_session, cy, co, "BETA-002", normal=20.0)
        r = client.get("/api/portfolio-health?pep_wbs=ALPHA-001").json()
        assert all(x["pep_wbs"] == "ALPHA-001" for x in r)

    # -- trends
    def test_trends_empty(self, client):
        assert client.get("/api/trends").json() == []

    def test_trends_chronological_order(self, client, db_session):
        # TrendItem has cycle_name but no cycle_start; seed with month-orderable names
        cy1 = _mk_cycle(db_session, "2026-01", 2026, 1)
        cy2 = _mk_cycle(db_session, "2026-02", 2026, 2)
        co = _mk_collab(db_session, "trend_co")
        _mk_record(db_session, cy1, co, "TR-001", normal=10.0)
        _mk_record(db_session, cy2, co, "TR-001", normal=20.0)
        result = client.get("/api/trends").json()
        names = [x["cycle_name"] for x in result]
        assert names == sorted(names)

    def test_trends_excludes_quarantine(self, client, db_session):
        cy = _mk_cycle(db_session, "Q", 2026, 3, quarantine=True)
        co = _mk_collab(db_session, "q_collab")
        _mk_record(db_session, cy, co, "Q-PEP")
        names = [x["cycle_name"] for x in client.get("/api/trends").json()]
        assert "Q" not in names

    def test_trends_cpi_field_present(self, client, db_session):
        self._seed_evm(db_session)
        result = client.get("/api/trends").json()
        for item in result:
            assert "cpi" in item  # may be None when no budgeted data

    def test_trends_actual_cost(self, client, db_session):
        self._seed_evm(db_session)
        result = client.get("/api/trends").json()
        total_cost = sum(x["actual_cost"] for x in result)
        assert total_cost == pytest.approx(7000.0)

    # -- allocation
    def test_allocation_empty(self, client):
        assert client.get("/api/allocation").json() == []

    def test_allocation_matrix(self, client, db_session):
        # AllocationItem is a flat row: collaborator, pep_wbs, total_hours, actual_cost
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        co = _mk_collab(db_session, "alloc_collab")
        _mk_record(db_session, cy, co, "ALLOC-001", normal=32.0, cost_per_hour=100.0)
        r = client.get("/api/allocation").json()
        item = next(x for x in r if x["collaborator"] == "alloc_collab" and x["pep_wbs"] == "ALLOC-001")
        assert item["total_hours"] == 32.0
        assert item["actual_cost"] == pytest.approx(3200.0)

    # -- forecast
    def test_forecast_requires_pep_wbs(self, client):
        assert client.get("/api/forecast").status_code == 422

    def test_forecast_pep_not_found(self, client):
        assert client.get("/api/forecast?pep_wbs=NONE-999").status_code == 404

    def test_forecast_returns_evm_metrics(self, client, db_session):
        # ForecastOut fields: consumed_hours, actual_cost, cpi, eac, spi, sv, history
        self._seed_evm(db_session)
        r = client.get("/api/forecast?pep_wbs=EVM-001")
        assert r.status_code == 200
        d = r.json()
        assert "cpi" in d
        assert "eac" in d
        assert "spi" in d
        assert "sv" in d
        assert "consumed_hours" in d
        assert "actual_cost" in d
        assert d["consumed_hours"] == pytest.approx(70.0)
        assert isinstance(d["history"], list)
        # spi/sv are None when no plan baseline exists
        assert d["spi"] is None
        assert d["sv"] is None


# ===========================================================================
# 9. PLANS — /api/projects/{id}/plans
# ===========================================================================

class TestPlans:
    def test_list_plans_empty(self, client, db_session):
        p = _mk_project(db_session, "PLAN-001")
        r = client.get(f"/api/projects/{p.id}/plans")
        assert r.status_code == 200
        assert r.json() == []

    def test_upsert_creates_plan(self, client, db_session):
        p = _mk_project(db_session, "PLAN-002")
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        # ProjectCyclePlanIn requires cycle_id in the body alongside planned_hours
        r = client.put(f"/api/projects/{p.id}/plans/{cy.id}",
                       json={"cycle_id": cy.id, "planned_hours": 80.0})
        assert r.status_code in (200, 201)
        assert r.json()["planned_hours"] == 80.0

    def test_upsert_updates_existing(self, client, db_session):
        p = _mk_project(db_session, "PLAN-003")
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        client.put(f"/api/projects/{p.id}/plans/{cy.id}", json={"cycle_id": cy.id, "planned_hours": 40.0})
        r = client.put(f"/api/projects/{p.id}/plans/{cy.id}", json={"cycle_id": cy.id, "planned_hours": 80.0})
        assert r.json()["planned_hours"] == 80.0

    def test_list_plans_after_upsert(self, client, db_session):
        p = _mk_project(db_session, "PLAN-004")
        cy1 = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        cy2 = _mk_cycle(db_session, "Feb/2026", 2026, 2)
        client.put(f"/api/projects/{p.id}/plans/{cy1.id}", json={"cycle_id": cy1.id, "planned_hours": 40.0})
        client.put(f"/api/projects/{p.id}/plans/{cy2.id}", json={"cycle_id": cy2.id, "planned_hours": 60.0})
        result = client.get(f"/api/projects/{p.id}/plans").json()
        assert len(result) == 2

    def test_delete_plan(self, client, db_session):
        p = _mk_project(db_session, "PLAN-005")
        cy = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        client.put(f"/api/projects/{p.id}/plans/{cy.id}", json={"cycle_id": cy.id, "planned_hours": 40.0})
        assert client.delete(f"/api/projects/{p.id}/plans/{cy.id}").status_code == 204
        assert client.get(f"/api/projects/{p.id}/plans").json() == []

    def test_plan_appears_in_forecast_pv(self, client, db_session):
        """Planned hours in ProjectCyclePlan surface as cumulative_planned_hours and enable SPI/SV."""
        cy1 = _mk_cycle(db_session, "Jan/2026", 2026, 1)
        cy2 = _mk_cycle(db_session, "Feb/2026", 2026, 2)
        p = _mk_project(db_session, "PLAN-PV", budget_h=100.0, budget_cost=10000.0)
        co = _mk_collab(db_session, "pv_collab")
        # collaborator has a rate so actual_cost > 0 (required for cpi/spi)
        from datetime import date as _date
        sl = _mk_level(db_session, "Sr-pv")
        _mk_rate(db_session, sl, 100.0, _date(2026, 1, 1))
        co.seniority_level_id = sl.id
        db_session.commit()
        _mk_record(db_session, cy1, co, "PLAN-PV", normal=30.0)
        client.put(f"/api/projects/{p.id}/plans/{cy1.id}", json={"cycle_id": cy1.id, "planned_hours": 40.0})
        client.put(f"/api/projects/{p.id}/plans/{cy2.id}", json={"cycle_id": cy2.id, "planned_hours": 30.0})
        r = client.get("/api/forecast?pep_wbs=PLAN-PV")
        assert r.status_code == 200
        d = r.json()
        history = d["history"]
        assert any(h.get("planned_hours") is not None for h in history)
        # With plan + budget + actual_cost: SPI and SV must be populated
        # consumed=30h out of 100h budget_h → EV = 30% × 10000 = 3000
        # planned=40h out of 100h budget_h → PV = 40% × 10000 = 4000
        # SPI = EV/PV = 3000/4000 = 0.75 (behind schedule)
        # SV  = EV - PV = -1000
        assert d["spi"] == pytest.approx(0.75, abs=0.01)
        assert d["sv"] == pytest.approx(-1000.0, abs=1.0)


# ===========================================================================
# 10. SENIORITY LEVELS — /api/seniority-levels
# ===========================================================================

class TestSeniorityLevels:
    def test_create_and_list(self, client):
        client.post("/api/seniority-levels", json={"name": "Sênior"})
        client.post("/api/seniority-levels", json={"name": "Pleno"})
        names = [x["name"] for x in client.get("/api/seniority-levels").json()]
        assert "Sênior" in names and "Pleno" in names

    def test_duplicate_rejected(self, client):
        client.post("/api/seniority-levels", json={"name": "Dup"})
        assert client.post("/api/seniority-levels", json={"name": "Dup"}).status_code == 409

    def test_update(self, client):
        sl = client.post("/api/seniority-levels", json={"name": "Old"}).json()
        r = client.put(f"/api/seniority-levels/{sl['id']}", json={"name": "New"})
        assert r.json()["name"] == "New"

    def test_delete_unused(self, client, db_session):
        sl = _mk_level(db_session, "Unused")
        assert client.delete(f"/api/seniority-levels/{sl.id}").status_code == 204

    def test_delete_in_use_rejected(self, client, db_session):
        sl = _mk_level(db_session, "InUse")
        _mk_collab(db_session, "linked", seniority_level=sl)
        assert client.delete(f"/api/seniority-levels/{sl.id}").status_code == 409


# ===========================================================================
# 11. RATE CARDS — /api/rate-cards
# ===========================================================================

class TestRateCards:
    def test_create(self, client, db_session):
        sl = _mk_level(db_session, "RC-Level")
        r = client.post("/api/rate-cards", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 120.0,
            "valid_from": "2026-01-01",
        })
        assert r.status_code == 201

    def test_invalid_date_range(self, client, db_session):
        sl = _mk_level(db_session, "RC-Level2")
        r = client.post("/api/rate-cards", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 100.0,
            "valid_from": "2026-06-01",
            "valid_to": "2026-01-01",
        })
        assert r.status_code == 422

    def test_filter_by_level(self, client, db_session):
        sl1 = _mk_level(db_session, "RC-L1")
        sl2 = _mk_level(db_session, "RC-L2")
        _mk_rate(db_session, sl1, 80.0, date(2026, 1, 1))
        _mk_rate(db_session, sl2, 160.0, date(2026, 1, 1))
        result = client.get(f"/api/rate-cards?seniority_level_id={sl1.id}").json()
        assert all(x["seniority_level_id"] == sl1.id for x in result)

    def test_update(self, client, db_session):
        sl = _mk_level(db_session, "RC-Upd")
        rc = _mk_rate(db_session, sl, 50.0, date(2026, 1, 1))
        r = client.put(f"/api/rate-cards/{rc.id}", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 75.0,
            "valid_from": "2026-01-01",
        })
        assert r.status_code == 200

    def test_delete(self, client, db_session):
        sl = _mk_level(db_session, "RC-Del")
        rc = _mk_rate(db_session, sl, 60.0, date(2026, 1, 1))
        assert client.delete(f"/api/rate-cards/{rc.id}").status_code == 204
        assert client.get("/api/rate-cards").json() == []


# ===========================================================================
# 12. TEAM — /api/team  &  /api/team/{id}/seniority
# ===========================================================================

class TestTeam:
    def test_list_empty(self, client):
        assert client.get("/api/team").json() == []

    def test_collaborator_shown_with_rate(self, client, db_session):
        sl = _mk_level(db_session, "TM-Level")
        _mk_rate(db_session, sl, 200.0, date(2026, 1, 1))
        _mk_collab(db_session, "TM-Pedro", seniority_level=sl)
        m = next(x for x in client.get("/api/team").json() if x["name"] == "TM-Pedro")
        assert m["current_hourly_rate"] == 200.0
        assert m["seniority_level_name"] == "TM-Level"

    def test_collaborator_without_seniority(self, client, db_session):
        _mk_collab(db_session, "TM-None")
        m = next(x for x in client.get("/api/team").json() if x["name"] == "TM-None")
        assert m["seniority_level_name"] is None
        assert m["current_hourly_rate"] is None

    def test_assign_seniority(self, client, db_session):
        sl = _mk_level(db_session, "TM-Assign")
        co = _mk_collab(db_session, "TM-Assign-Co")
        r = client.put(f"/api/team/{co.id}/seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 200
        assert r.json()["seniority_level_id"] == sl.id

    def test_clear_seniority(self, client, db_session):
        sl = _mk_level(db_session, "TM-Clear")
        co = _mk_collab(db_session, "TM-Clear-Co", seniority_level=sl)
        r = client.put(f"/api/team/{co.id}/seniority", json={"seniority_level_id": None})
        assert r.json()["seniority_level_id"] is None

    def test_bulk_seniority_assign(self, client, db_session):
        """bulk-seniority is admin-only; conftest client runs as admin."""
        sl = _mk_level(db_session, "TM-Bulk")
        _mk_collab(db_session, "Bulk1")
        _mk_collab(db_session, "Bulk2")
        r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 200
        assigned = [m for m in r.json() if m["seniority_level_id"] == sl.id]
        assert len(assigned) >= 2

    def test_bulk_clear_seniority(self, client, db_session):
        sl = _mk_level(db_session, "TM-BulkClr")
        _mk_collab(db_session, "BulkClr1", seniority_level=sl)
        r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": None})
        assert r.status_code == 200
        assert all(m["seniority_level_id"] is None for m in r.json())

    def test_non_admin_cannot_bulk_assign(self, db_session):
        sl = _mk_level(db_session, "TM-BulkFail")
        regular = _mk_user(db_session, "bulk_nonadmin")
        with _acting_as(regular) as c:
            r = c.put("/api/team/bulk-seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 403


# ===========================================================================
# 13. GLOBAL CONFIG — /api/config
# ===========================================================================

class TestGlobalConfig:
    def test_get_defaults(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200
        d = r.json()
        assert d["extra_hours_multiplier"] > 0
        assert d["standby_hours_multiplier"] > 0

    def test_update_multipliers(self, client):
        """PUT /api/config is admin-only; conftest client runs as admin."""
        r = client.put("/api/config",
                       json={"extra_hours_multiplier": 2.5, "standby_hours_multiplier": 0.33})
        assert r.status_code == 200
        assert r.json()["extra_hours_multiplier"] == 2.5

    def test_zero_multiplier_rejected(self, client):
        r = client.put("/api/config",
                       json={"extra_hours_multiplier": 0, "standby_hours_multiplier": 1})
        assert r.status_code == 422

    def test_non_admin_forbidden(self, db_session):
        u = _mk_user(db_session, "cfg_user")
        with _acting_as(u) as c:
            r = c.put("/api/config", json={"extra_hours_multiplier": 2.0, "standby_hours_multiplier": 1.0})
        assert r.status_code == 403

    def test_multipliers_affect_actual_cost(self, client, db_session):
        client.put("/api/config", json={"extra_hours_multiplier": 2.0, "standby_hours_multiplier": 1.0})
        cy = _mk_cycle(db_session, "Config-Cy", 2026, 3)
        sl = _mk_level(db_session, "CFG-Level")
        _mk_rate(db_session, sl, 100.0, date(2026, 1, 1))
        co = _mk_collab(db_session, "cfg_collab", seniority_level=sl)
        # 4h extra × R$100 × 2.0 multiplier = R$800  (normal=0.0 to override default 8h)
        _mk_record(db_session, cy, co, "CFG-001", normal=0.0, extra=4.0, cost_per_hour=100.0)
        item = next(x for x in client.get("/api/portfolio-health").json() if x["pep_wbs"] == "CFG-001")
        assert item["actual_cost"] == pytest.approx(800.0)


# ===========================================================================
# 14. AUDIT LOG — GET /api/audit-log
# ===========================================================================

class TestAuditLog:
    def test_empty(self, client):
        r = client.get("/api/audit-log")
        assert r.status_code == 200
        assert r.json() == []

    def test_entries_recorded_on_cycle_create(self, client):
        client.post("/api/cycles", json={
            "name": "Audit-Cy",
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        })
        log = client.get("/api/audit-log").json()
        assert any(e["entity"] == "cycle" for e in log)

    def test_filter_by_entity(self, client):
        client.post("/api/projects", json={"pep_wbs": "AUD-001", "name": "AudProj", "status": "ativo"})
        client.post("/api/cycles", json={"name": "AudCy", "start_date": "2026-07-01", "end_date": "2026-07-31"})
        proj_log = client.get("/api/audit-log?entity=project").json()
        assert all(e["entity"] == "project" for e in proj_log)

    def test_filter_by_action(self, client):
        client.post("/api/cycles", json={
            "name": "ActFilter",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        })
        log = client.get("/api/audit-log?action=create").json()
        assert all(e["action"] == "create" for e in log)

    def test_non_admin_forbidden(self, db_session):
        u = _mk_user(db_session, "nonadmin_audit")
        with _acting_as(u) as c:
            r = c.get("/api/audit-log")
        assert r.status_code == 403

    def test_pagination(self, client):
        for i in range(5):
            client.post("/api/seniority-levels", json={"name": f"Pag-{i}"})
        page1 = client.get("/api/audit-log?limit=3&offset=0").json()
        page2 = client.get("/api/audit-log?limit=3&offset=3").json()
        assert len(page1) <= 3
        ids1 = {e["id"] for e in page1}
        ids2 = {e["id"] for e in page2}
        assert ids1.isdisjoint(ids2)


# ===========================================================================
# 15. FULL LIFECYCLE — end-to-end scenario
# ===========================================================================

class TestFullLifecycle:
    """
    Simulates the complete PM workflow:
      1. Bootstrap rate card + project
      2. Import two monthly timesheets
      3. Assign plans (PV baseline)
      4. Read all analytics and verify EVM numbers
      5. Archive past cycle
      6. Verify audit trail
    """

    def test_full_workflow(self, client, db_session):
        # ---- 1. Rate card setup ----------------------------------------
        sl_r = client.post("/api/seniority-levels", json={"name": "Sênior"}).json()
        client.post("/api/rate-cards", json={
            "seniority_level_id": sl_r["id"],
            "hourly_rate": 100.0,
            "valid_from": "2026-01-01",
        })

        # ---- 2. Project --------------------------------------------------
        proj_r = client.post("/api/projects", json={
            "pep_wbs": "LIFE-001",
            "name": "Lifecycle Proj",
            "status": "ativo",
            "budget_hours": 80.0,
            "budget_cost": 8000.0,
        }).json()
        assert proj_r["pep_wbs"] == "LIFE-001"

        # ---- 3. Two cycles -----------------------------------------------
        cy1_r = client.post("/api/cycles", json={
            "name": "Jan/2026", "start_date": "2026-01-01", "end_date": "2026-01-31"
        }).json()
        cy2_r = client.post("/api/cycles", json={
            "name": "Feb/2026", "start_date": "2026-02-01", "end_date": "2026-02-28"
        }).json()

        # ---- 4. Assign seniority to collaborator before upload -----------
        sl = db_session.query(SeniorityLevel).filter_by(name="Sênior").first()
        collab_name = "Life Collab"

        # ---- 5. Upload timesheets ----------------------------------------
        data_jan = _csv([(collab_name, "15/01/2026", 20.0, 0, 0, "LIFE-001", "Lifecycle Proj")])
        r_jan = client.post("/api/upload-timesheet", files={"file": ("jan.csv", data_jan, "text/csv")})
        assert r_jan.json()["records_inserted"] >= 1

        # Assign seniority so Feb upload freezes the correct rate
        co = db_session.query(Collaborator).filter_by(name=collab_name).first()
        co.seniority_level_id = sl.id
        db_session.commit()

        data_feb = _csv([(collab_name, "15/02/2026", 15.0, 0, 0, "LIFE-001", "Lifecycle Proj")])
        r_feb = client.post("/api/upload-timesheet", files={"file": ("feb.csv", data_feb, "text/csv")})
        assert r_feb.json()["records_inserted"] >= 1

        # ---- 6. Set PV plans ---------------------------------------------
        client.put(f"/api/projects/{proj_r['id']}/plans/{cy1_r['id']}",
                   json={"cycle_id": cy1_r["id"], "planned_hours": 40.0})
        client.put(f"/api/projects/{proj_r['id']}/plans/{cy2_r['id']}",
                   json={"cycle_id": cy2_r["id"], "planned_hours": 40.0})

        # ---- 7. Check portfolio health -----------------------------------
        health = client.get("/api/portfolio-health?pep_wbs=LIFE-001").json()
        item = next(x for x in health if x["pep_wbs"] == "LIFE-001")
        assert item["consumed_hours"] == 35.0   # 20h Jan + 15h Feb
        assert item["budget_hours"] == 80.0

        # ---- 8. Check trends (TrendItem has normal/extra/standby_hours, no total_hours) ----
        trends = client.get("/api/trends?pep_wbs=LIFE-001").json()
        total_h = sum(t["normal_hours"] + t["extra_hours"] + t["standby_hours"] for t in trends)
        assert total_h == 35.0

        # ---- 9. Forecast EVM metrics (ForecastOut has consumed_hours, not ev/ac) ---------
        forecast = client.get("/api/forecast?pep_wbs=LIFE-001").json()
        assert forecast["consumed_hours"] == pytest.approx(35.0)
        history = forecast["history"]
        assert any(h.get("planned_hours") is not None for h in history)

        # ---- 10. Archive Jan cycle ---------------------------------------
        r_arch = client.patch(f"/api/cycles/{cy1_r['id']}/toggle-archive")
        assert r_arch.json()["is_active"] is False
        active_names = [c["name"] for c in client.get("/api/cycles").json()]
        assert "Jan/2026" not in active_names
        # Analytics are unaffected by archiving
        health_after = client.get("/api/portfolio-health?pep_wbs=LIFE-001").json()
        item_after = next(x for x in health_after if x["pep_wbs"] == "LIFE-001")
        assert item_after["consumed_hours"] == 35.0

        # ---- 11. Audit trail has entries ---------------------------------
        log = client.get("/api/audit-log").json()
        entities = {e["entity"] for e in log}
        assert "cycle" in entities
        assert "project" in entities
