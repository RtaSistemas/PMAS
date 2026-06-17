"""Tests for POST /api/v2/projects/{project_id}/simulate — What-If Simulation (F11)."""
from __future__ import annotations

import math
from datetime import date

import pytest

from backend.app.models import (
    Collaborator, Cycle, Project, RateCard, SeniorityLevel, TimesheetRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cycle(db, name, start, end):
    c = Cycle(name=name, start_date=start, end_date=end)
    db.add(c)
    db.flush()
    return c


def _make_project(db, pep, name, budget_hours=None, budget_cost=None):
    p = Project(pep_wbs=pep, name=name, budget_hours=budget_hours, budget_cost=budget_cost)
    db.add(p)
    db.flush()
    return p


def _make_collab(db, name, rate=50.0):
    sl = SeniorityLevel(name=f"SL-sim-{name}")
    db.add(sl)
    db.flush()
    collab = Collaborator(name=name, seniority_level_id=sl.id)
    db.add(collab)
    db.flush()
    rc = RateCard(seniority_level_id=sl.id, hourly_rate=rate, valid_from=date(2024, 1, 1))
    db.add(rc)
    db.flush()
    return collab


def _make_record(db, collab, cycle, pep, normal_h, rate=50.0):
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=cycle.start_date,
        pep_wbs=pep,
        pep_description=f"Desc {pep}",
        normal_hours=normal_h,
        extra_hours=0.0,
        standby_hours=0.0,
        cost_per_hour=rate,
        normal_cost=round(normal_h * rate, 4),
        extra_cost=0.0,
        standby_cost=0.0,
    )
    db.add(r)
    db.flush()
    return r


def _simulate(client, project_id, **kwargs):
    return client.post(f"/api/v2/projects/{project_id}/simulate", json=kwargs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSimulate:

    def test_404_for_unknown_project(self, client, clean_db):
        r = _simulate(client, 99999)
        assert r.status_code == 404

    def test_no_data_returns_zeros(self, client, db_session, clean_db):
        proj = _make_project(db_session, "SIM-001", "No Data", budget_hours=100.0)
        db_session.commit()

        r = _simulate(client, proj.id)
        assert r.status_code == 200
        body = r.json()
        assert body["consumed_hours"] == pytest.approx(0.0)
        assert body["consumed_cost"] == pytest.approx(0.0)
        assert body["avg_velocity"] == pytest.approx(0.0)
        assert body["sim_velocity"] == pytest.approx(0.0)
        assert body["cycles_to_complete"] is None
        assert body["burn_up_projected"] == []

    def test_default_multiplier_cycles_to_complete(self, client, db_session, clean_db):
        """velocity_multiplier=1.0 → cycles_to_complete = ceil(remaining / avg_velocity)."""
        proj = _make_project(db_session, "SIM-002", "Default Mult", budget_hours=200.0)
        collab = _make_collab(db_session, "SimUser1")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        c3 = _make_cycle(db_session, "MAR/2025", date(2025, 3, 1), date(2025, 3, 31))
        _make_record(db_session, collab, c1, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c3, proj.pep_wbs, 20.0)
        db_session.commit()

        r = _simulate(client, proj.id, velocity_multiplier=1.0)
        assert r.status_code == 200
        body = r.json()

        # consumed = 60h, remaining = 140h, avg_velocity = 20h
        assert body["consumed_hours"] == pytest.approx(60.0)
        assert body["remaining_hours"] == pytest.approx(140.0)
        assert body["avg_velocity"] == pytest.approx(20.0)
        assert body["sim_velocity"] == pytest.approx(20.0)
        expected_cycles = math.ceil(140.0 / 20.0)  # = 7
        assert body["cycles_to_complete"] == expected_cycles

    def test_velocity_multiplier_2_halves_cycles(self, client, db_session, clean_db):
        """velocity_multiplier=2.0 → sim_velocity doubles → cycles_to_complete halves."""
        proj = _make_project(db_session, "SIM-003", "Double Mult", budget_hours=200.0)
        collab = _make_collab(db_session, "SimUser2")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        _make_record(db_session, collab, c1, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 20.0)
        db_session.commit()

        r1 = _simulate(client, proj.id, velocity_multiplier=1.0)
        r2 = _simulate(client, proj.id, velocity_multiplier=2.0)
        assert r1.status_code == 200
        assert r2.status_code == 200

        b1 = r1.json()
        b2 = r2.json()

        assert b2["sim_velocity"] == pytest.approx(b1["avg_velocity"] * 2.0)
        # Doubling velocity should approximately halve the cycles (ceiling rounding may differ by 1)
        assert b2["cycles_to_complete"] <= b1["cycles_to_complete"]

    def test_extra_hours_per_cycle_increases_velocity(self, client, db_session, clean_db):
        """extra_hours_per_cycle is added to sim_velocity."""
        proj = _make_project(db_session, "SIM-004", "Extra Hours", budget_hours=100.0)
        collab = _make_collab(db_session, "SimUser3")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_record(db_session, collab, c1, proj.pep_wbs, 10.0)
        db_session.commit()

        r_base  = _simulate(client, proj.id, velocity_multiplier=1.0, extra_hours_per_cycle=0.0)
        r_extra = _simulate(client, proj.id, velocity_multiplier=1.0, extra_hours_per_cycle=5.0)
        assert r_base.status_code == 200
        assert r_extra.status_code == 200

        b_base  = r_base.json()
        b_extra = r_extra.json()

        # sim_velocity should be 5h higher
        assert b_extra["sim_velocity"] == pytest.approx(b_base["sim_velocity"] + 5.0)
        # Fewer cycles needed with extra velocity
        assert b_extra["cycles_to_complete"] <= b_base["cycles_to_complete"]

    def test_auth_required(self):
        """Unauthenticated request should return 401."""
        from fastapi.testclient import TestClient
        from backend.app.main import app
        from backend.app.database import get_db
        from backend.app.deps import get_current_user

        # Remove auth override temporarily
        saved = dict(app.dependency_overrides)
        # Keep only get_db override, remove get_current_user override
        from tests.conftest import _override_get_db
        app.dependency_overrides = {get_db: _override_get_db}
        try:
            with TestClient(app, raise_server_exceptions=False) as c:
                r = c.post("/api/v2/projects/1/simulate", json={})
            assert r.status_code == 401
        finally:
            app.dependency_overrides = saved

    def test_projected_eac_cost_matches_compute_eac_avg_rate(self, client, db_session, clean_db):
        """projected_eac_cost must equal compute_eac_avg_rate(AC, consumed_h, remaining_h)."""
        from backend.app.services.evm import compute_eac_avg_rate
        proj = _make_project(db_session, "SIM-EAC", "EAC Test", budget_hours=150.0, budget_cost=7_500.0)
        collab = _make_collab(db_session, "SimEACUser", rate=50.0)
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        _make_record(db_session, collab, c1, proj.pep_wbs, 30.0, rate=50.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 20.0, rate=50.0)
        db_session.commit()

        r = _simulate(client, proj.id, velocity_multiplier=1.0)
        assert r.status_code == 200
        body = r.json()

        consumed_cost = body["consumed_cost"]   # 50*30 + 50*20 = 2500
        consumed_hours = body["consumed_hours"]  # 50
        remaining = body["remaining_hours"]       # 100

        expected = compute_eac_avg_rate(consumed_cost, consumed_hours, remaining)
        assert body["projected_eac_cost"] == pytest.approx(expected)

    def test_burn_up_projected_length_matches_cycles(self, client, db_session, clean_db):
        """burn_up_projected should have exactly cycles_to_complete entries."""
        proj = _make_project(db_session, "SIM-005", "BurnUp", budget_hours=100.0)
        collab = _make_collab(db_session, "SimUser4")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        _make_record(db_session, collab, c1, proj.pep_wbs, 10.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 10.0)
        db_session.commit()

        r = _simulate(client, proj.id, velocity_multiplier=1.0)
        assert r.status_code == 200
        body = r.json()

        if body["cycles_to_complete"] is not None and body["cycles_to_complete"] > 0:
            assert len(body["burn_up_projected"]) == body["cycles_to_complete"]
