"""Tests for GET /api/v2/projects/{project_id}/monte-carlo — Monte Carlo Simulation (F4)."""
from __future__ import annotations

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
    sl = SeniorityLevel(name=f"SL-mc-{name}")
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


def _mc(client, project_id, **params):
    return client.get(f"/api/v2/projects/{project_id}/monte-carlo", params=params)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMonteCarlo:

    def test_404_for_unknown_project(self, client, clean_db):
        r = _mc(client, 99999)
        assert r.status_code == 404

    def test_no_data_returns_insufficient_data(self, client, db_session, clean_db):
        proj = _make_project(db_session, "MC-001", "No Data", budget_hours=100.0)
        db_session.commit()

        r = _mc(client, proj.id)
        assert r.status_code == 200
        body = r.json()
        assert body["error"] == "insufficient_data"
        assert body["p10"] is None
        assert body["p50"] is None
        assert body["p90"] is None

    def test_one_cycle_returns_insufficient_data(self, client, db_session, clean_db):
        proj = _make_project(db_session, "MC-002", "One Cycle", budget_hours=100.0)
        collab = _make_collab(db_session, "MCUser1")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_record(db_session, collab, c1, proj.pep_wbs, 10.0)
        db_session.commit()

        r = _mc(client, proj.id)
        assert r.status_code == 200
        body = r.json()
        assert body["error"] == "insufficient_data"

    def test_p10_le_p50_le_p90(self, client, db_session, clean_db):
        """With sufficient data: p10 <= p50 <= p90."""
        proj = _make_project(db_session, "MC-003", "Multi Cycle", budget_hours=500.0)
        collab = _make_collab(db_session, "MCUser2")
        cycles_data = [
            ("JAN/2025", date(2025, 1, 1), date(2025, 1, 31), 20.0),
            ("FEV/2025", date(2025, 2, 1), date(2025, 2, 28), 25.0),
            ("MAR/2025", date(2025, 3, 1), date(2025, 3, 31), 18.0),
            ("ABR/2025", date(2025, 4, 1), date(2025, 4, 30), 22.0),
        ]
        for name, start, end, hours in cycles_data:
            cy = _make_cycle(db_session, name, start, end)
            _make_record(db_session, collab, cy, proj.pep_wbs, hours)
        db_session.commit()

        r = _mc(client, proj.id, seed=42)
        assert r.status_code == 200
        body = r.json()

        assert body["error"] is None
        assert body["p10"] is not None
        assert body["p50"] is not None
        assert body["p90"] is not None
        assert body["p10"] <= body["p50"] <= body["p90"]

    def test_remaining_zero_returns_zeros(self, client, db_session, clean_db):
        """When consumed >= budget, all percentiles should be 0."""
        proj = _make_project(db_session, "MC-004", "Done", budget_hours=40.0)
        collab = _make_collab(db_session, "MCUser3")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        _make_record(db_session, collab, c1, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 20.0)
        db_session.commit()

        r = _mc(client, proj.id, seed=42)
        assert r.status_code == 200
        body = r.json()

        assert body["p10"] == 0
        assert body["p50"] == 0
        assert body["p90"] == 0
        assert body["remaining_hours"] == pytest.approx(0.0)

    def test_auth_required(self):
        """Unauthenticated request should return 401."""
        from fastapi.testclient import TestClient
        from backend.app.main import app
        from backend.app.database import get_db
        from backend.app.deps import get_current_user

        saved = dict(app.dependency_overrides)
        from tests.conftest import _override_get_db
        app.dependency_overrides = {get_db: _override_get_db}
        try:
            with TestClient(app, raise_server_exceptions=False) as c:
                r = c.get("/api/v2/projects/1/monte-carlo")
            assert r.status_code == 401
        finally:
            app.dependency_overrides = saved

    def test_custom_iterations_param(self, client, db_session, clean_db):
        """Custom iterations param is reflected in response and changes result precision."""
        proj = _make_project(db_session, "MC-005", "Iters", budget_hours=500.0)
        collab = _make_collab(db_session, "MCUser4")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        c3 = _make_cycle(db_session, "MAR/2025", date(2025, 3, 1), date(2025, 3, 31))
        _make_record(db_session, collab, c1, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 25.0)
        _make_record(db_session, collab, c3, proj.pep_wbs, 22.0)
        db_session.commit()

        r = _mc(client, proj.id, iterations=500, seed=42)
        assert r.status_code == 200
        body = r.json()
        assert body["iterations"] == 500
        assert body["error"] is None

    def test_mean_velocity_and_stdev_returned(self, client, db_session, clean_db):
        """mean_velocity and stdev_velocity are returned with valid data."""
        proj = _make_project(db_session, "MC-006", "Stats", budget_hours=200.0)
        collab = _make_collab(db_session, "MCUser5")
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        c3 = _make_cycle(db_session, "MAR/2025", date(2025, 3, 1), date(2025, 3, 31))
        _make_record(db_session, collab, c1, proj.pep_wbs, 10.0)
        _make_record(db_session, collab, c2, proj.pep_wbs, 20.0)
        _make_record(db_session, collab, c3, proj.pep_wbs, 30.0)
        db_session.commit()

        r = _mc(client, proj.id, seed=42)
        assert r.status_code == 200
        body = r.json()

        assert body["mean_velocity"] is not None
        assert body["stdev_velocity"] is not None
        assert body["mean_velocity"] > 0
        assert body["stdev_velocity"] > 0
        # mean of [10, 20, 30] = 20.0
        assert body["mean_velocity"] == pytest.approx(20.0, abs=0.01)
