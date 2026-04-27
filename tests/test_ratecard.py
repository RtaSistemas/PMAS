from __future__ import annotations

from datetime import date
from io import BytesIO

import pytest

from contextlib import contextmanager

from backend.app.deps import get_current_user
from backend.app.main import app
from backend.app.models import Collaborator, Cycle, GlobalConfig, RateCard, SeniorityLevel, TimesheetRecord, User
from backend.app.routers.auth import hash_password


@contextmanager
def _acting_as(user):
    saved = dict(app.dependency_overrides)
    app.dependency_overrides[get_current_user] = lambda: user
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _level(db, name):
    sl = SeniorityLevel(name=name)
    db.add(sl); db.commit(); db.refresh(sl)
    return sl


def _rate(db, level, rate, valid_from, valid_to=None):
    rc = RateCard(
        seniority_level_id=level.id,
        hourly_rate=rate,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    db.add(rc); db.commit(); db.refresh(rc)
    return rc


def _collab(db, name, seniority_level=None):
    c = Collaborator(name=name, seniority_level_id=seniority_level.id if seniority_level else None)
    db.add(c); db.commit(); db.refresh(c)
    return c


def _csv_bytes(name="João", date_str="15/01/2026", hours=8.0):
    content = f"Colaborador,Data,Horas totais (decimal)\n{name},{date_str},{hours}"
    return content.encode()


# ===========================================================================
# /api/seniority-levels
# ===========================================================================

class TestSeniorityLevels:
    def test_empty(self, client):
        assert client.get("/api/seniority-levels").json() == []

    def test_create(self, client):
        r = client.post("/api/seniority-levels", json={"name": "Sênior"})
        assert r.status_code == 201
        assert r.json()["name"] == "Sênior"

    def test_list(self, client):
        client.post("/api/seniority-levels", json={"name": "Pleno"})
        client.post("/api/seniority-levels", json={"name": "Júnior"})
        names = [l["name"] for l in client.get("/api/seniority-levels").json()]
        assert "Pleno" in names and "Júnior" in names

    def test_create_duplicate_rejected(self, client):
        client.post("/api/seniority-levels", json={"name": "Sênior"})
        r = client.post("/api/seniority-levels", json={"name": "Sênior"})
        assert r.status_code == 409

    def test_update(self, client):
        sl = client.post("/api/seniority-levels", json={"name": "Old"}).json()
        r = client.put(f"/api/seniority-levels/{sl['id']}", json={"name": "New"})
        assert r.status_code == 200
        assert r.json()["name"] == "New"

    def test_delete(self, client, db_session):
        sl = _level(db_session, "Temp")
        r = client.delete(f"/api/seniority-levels/{sl.id}")
        assert r.status_code == 204
        assert client.get("/api/seniority-levels").json() == []

    def test_delete_in_use_rejected(self, client, db_session):
        sl = _level(db_session, "InUse")
        _collab(db_session, "Ana", seniority_level=sl)
        r = client.delete(f"/api/seniority-levels/{sl.id}")
        assert r.status_code == 409

    def test_delete_not_found(self, client):
        assert client.delete("/api/seniority-levels/9999").status_code == 404


# ===========================================================================
# /api/rate-cards
# ===========================================================================

class TestRateCards:
    def test_empty(self, client):
        assert client.get("/api/rate-cards").json() == []

    def test_create(self, client, db_session):
        sl = _level(db_session, "Sênior")
        r = client.post("/api/rate-cards", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 150.0,
            "valid_from": "2026-01-01",
            "valid_to": None,
        })
        assert r.status_code == 201

    def test_create_invalid_date_range(self, client, db_session):
        sl = _level(db_session, "Pleno")
        r = client.post("/api/rate-cards", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 100.0,
            "valid_from": "2026-06-01",
            "valid_to": "2026-01-01",
        })
        assert r.status_code == 422

    def test_create_unknown_level(self, client):
        r = client.post("/api/rate-cards", json={
            "seniority_level_id": 9999,
            "hourly_rate": 100.0,
            "valid_from": "2026-01-01",
        })
        assert r.status_code == 404

    def test_filter_by_level(self, client, db_session):
        sl1 = _level(db_session, "L1")
        sl2 = _level(db_session, "L2")
        _rate(db_session, sl1, 100.0, date(2026, 1, 1))
        _rate(db_session, sl2, 200.0, date(2026, 1, 1))
        result = client.get(f"/api/rate-cards?seniority_level_id={sl1.id}").json()
        assert all(r["seniority_level_id"] == sl1.id for r in result)

    def test_delete(self, client, db_session):
        sl = _level(db_session, "Del")
        rc = _rate(db_session, sl, 50.0, date(2026, 1, 1))
        assert client.delete(f"/api/rate-cards/{rc.id}").status_code == 204
        assert client.get("/api/rate-cards").json() == []

    def test_update(self, client, db_session):
        sl = _level(db_session, "Up")
        rc = _rate(db_session, sl, 80.0, date(2026, 1, 1))
        r = client.put(f"/api/rate-cards/{rc.id}", json={
            "seniority_level_id": sl.id,
            "hourly_rate": 99.0,
            "valid_from": "2026-01-01",
        })
        assert r.status_code == 200
        assert client.get("/api/rate-cards").json()[0]["hourly_rate"] == 99.0


# ===========================================================================
# /api/team
# ===========================================================================

class TestTeam:
    def test_empty(self, client):
        assert client.get("/api/team").json() == []

    def test_returns_collaborators(self, client, db_session):
        _collab(db_session, "Maria")
        result = client.get("/api/team").json()
        assert any(m["name"] == "Maria" for m in result)

    def test_collab_with_seniority_and_rate(self, client, db_session):
        sl = _level(db_session, "Sênior")
        _rate(db_session, sl, 150.0, date(2026, 1, 1))
        _collab(db_session, "Pedro", seniority_level=sl)
        result = client.get("/api/team").json()
        m = next(x for x in result if x["name"] == "Pedro")
        assert m["seniority_level_name"] == "Sênior"
        assert m["current_hourly_rate"] == 150.0

    def test_collab_without_seniority(self, client, db_session):
        _collab(db_session, "Lucas")
        result = client.get("/api/team").json()
        m = next(x for x in result if x["name"] == "Lucas")
        assert m["seniority_level_name"] is None
        assert m["current_hourly_rate"] is None

    def test_assign_seniority(self, client, db_session):
        sl = _level(db_session, "Pleno")
        c = _collab(db_session, "Carla")
        r = client.put(f"/api/team/{c.id}/seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 200
        assert r.json()["seniority_level_id"] == sl.id

    def test_assign_unknown_seniority_rejected(self, client, db_session):
        c = _collab(db_session, "Alvo")
        r = client.put(f"/api/team/{c.id}/seniority", json={"seniority_level_id": 9999})
        assert r.status_code == 404

    def test_clear_seniority(self, client, db_session):
        sl = _level(db_session, "X")
        c = _collab(db_session, "Removido", seniority_level=sl)
        r = client.put(f"/api/team/{c.id}/seniority", json={"seniority_level_id": None})
        assert r.status_code == 200
        assert r.json()["seniority_level_id"] is None


# ===========================================================================
# Rate lookup during ingestion
# ===========================================================================

class TestRateLookupIngestion:
    def _make_cycle(self, db):
        c = Cycle(name="Jan/2026", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31), is_quarantine=False)
        db.add(c); db.commit()

    def test_no_seniority_gives_zero_cost(self, client, db_session):
        self._make_cycle(db_session)
        data = _csv_bytes("NaoSenior", "15/01/2026", 8.0)
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.status_code == 200
        rec = db_session.query(TimesheetRecord).first()
        assert rec.cost_per_hour == 0.0

    def test_seniority_with_rate_gives_correct_cost(self, client, db_session):
        self._make_cycle(db_session)
        sl = _level(db_session, "Sênior")
        _rate(db_session, sl, 120.0, date(2026, 1, 1))
        collab = _collab(db_session, "ComTaxa", seniority_level=sl)
        data = _csv_bytes("ComTaxa", "15/01/2026", 8.0)
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.status_code == 200
        rec = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.collaborator_id == collab.id
        ).first()
        assert rec.cost_per_hour == 120.0

    def test_expired_rate_gives_zero_cost(self, client, db_session):
        self._make_cycle(db_session)
        sl = _level(db_session, "Expirado")
        _rate(db_session, sl, 80.0, date(2025, 1, 1), date(2025, 12, 31))
        collab = _collab(db_session, "Expirado", seniority_level=sl)
        data = _csv_bytes("Expirado", "15/01/2026", 8.0)
        r = client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        assert r.status_code == 200
        rec = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.collaborator_id == collab.id
        ).first()
        assert rec.cost_per_hour == 0.0

    def test_rate_frozen_after_rate_change(self, client, db_session):
        self._make_cycle(db_session)
        sl = _level(db_session, "Congelado")
        _rate(db_session, sl, 100.0, date(2026, 1, 1))
        collab = _collab(db_session, "Congelado", seniority_level=sl)
        data = _csv_bytes("Congelado", "15/01/2026", 8.0)
        client.post("/api/upload-timesheet", files={"file": ("t.csv", data, "text/csv")})
        rec = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.collaborator_id == collab.id
        ).first()
        assert rec.cost_per_hour == 100.0
        # Even if rate changes later, stored cost_per_hour stays frozen
        rc = db_session.query(RateCard).first()
        rc.hourly_rate = 999.0
        db_session.commit()
        db_session.refresh(rec)
        assert rec.cost_per_hour == 100.0


# ===========================================================================
# Bulk seniority assignment
# ===========================================================================

class TestBulkSeniority:
    def _make_collabs(self, db_session, names):
        collabs = []
        for n in names:
            c = Collaborator(name=n)
            db_session.add(c)
        db_session.commit()
        for n in names:
            collabs.append(db_session.query(Collaborator).filter_by(name=n).first())
        return collabs

    def test_assigns_level_to_all(self, client, db_session):
        sl = _level(db_session, "Pleno")
        self._make_collabs(db_session, ["Alice", "Bob", "Carol"])
        r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 200
        names_with_level = [m["name"] for m in r.json() if m["seniority_level_id"] == sl.id]
        assert set(names_with_level) == {"Alice", "Bob", "Carol"}

    def test_clears_all_seniority(self, client, db_session):
        sl = _level(db_session, "Senior")
        self._make_collabs(db_session, ["Dave", "Eve"])
        client.put("/api/team/bulk-seniority", json={"seniority_level_id": sl.id})
        r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": None})
        assert r.status_code == 200
        assert all(m["seniority_level_id"] is None for m in r.json())

    def test_unknown_level_rejected(self, client):
        r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": 99999})
        assert r.status_code == 404

    def test_non_admin_forbidden(self, db_session):
        regular = User(username="reguser", hashed_password=hash_password("pass"), role="user")
        db_session.add(regular); db_session.commit(); db_session.refresh(regular)
        sl = _level(db_session, "Junior")
        with _acting_as(regular) as c:
            r = c.put("/api/team/bulk-seniority", json={"seniority_level_id": sl.id})
        assert r.status_code == 403


# ===========================================================================
# Global config (multipliers)
# ===========================================================================

class TestGlobalConfig:
    def test_get_returns_defaults(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200
        d = r.json()
        assert d["extra_hours_multiplier"] > 0
        assert d["standby_hours_multiplier"] > 0

    def test_put_updates_values(self, client):
        r = client.put("/api/config", json={"extra_hours_multiplier": 2.0, "standby_hours_multiplier": 0.5})
        assert r.status_code == 200
        d = r.json()
        assert d["extra_hours_multiplier"] == 2.0
        assert d["standby_hours_multiplier"] == 0.5

    def test_put_zero_multiplier_rejected(self, client):
        r = client.put("/api/config", json={"extra_hours_multiplier": 0, "standby_hours_multiplier": 1.0})
        assert r.status_code == 422

    def test_put_non_admin_forbidden(self, db_session):
        regular = User(username="cfguser", hashed_password=hash_password("pass"), role="user")
        db_session.add(regular); db_session.commit(); db_session.refresh(regular)
        with _acting_as(regular) as c:
            r = c.put("/api/config", json={"extra_hours_multiplier": 2.0, "standby_hours_multiplier": 1.0})
        assert r.status_code == 403

    def test_multipliers_applied_to_actual_cost(self, client, db_session):
        """extra_hours at 2x should double the extra-hours cost component."""
        # Set multipliers
        client.put("/api/config", json={"extra_hours_multiplier": 2.0, "standby_hours_multiplier": 1.0})
        # Create cycle, seniority, rate card, collaborator
        cycle = Cycle(name="TestMult", start_date=date(2026, 3, 1), end_date=date(2026, 3, 31))
        db_session.add(cycle); db_session.commit(); db_session.refresh(cycle)
        sl = _level(db_session, "MultLevel")
        _rate(db_session, sl, 100.0, date(2026, 1, 1))
        collab = Collaborator(name="MultCollab", seniority_level_id=sl.id)
        db_session.add(collab); db_session.commit(); db_session.refresh(collab)
        # Insert record with 4h extra at R$100/h — with 2x multiplier, cost = 4 * 100 * 2 = 800
        rec = TimesheetRecord(
            collaborator_id=collab.id, cycle_id=cycle.id,
            record_date=date(2026, 3, 10),
            pep_wbs="60OP-MULT", pep_description="Mult Test",
            normal_hours=0.0, extra_hours=4.0, standby_hours=0.0,
            cost_per_hour=100.0,
        )
        db_session.add(rec); db_session.commit()
        r = client.get("/api/portfolio-health")
        item = next((x for x in r.json() if x["pep_wbs"] == "60OP-MULT"), None)
        assert item is not None
        assert item["actual_cost"] == pytest.approx(800.0)
