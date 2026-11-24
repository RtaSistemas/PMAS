"""Regression tests for the analytics audit findings (B3-B14).

Each class reproduces one finding.  See the commit message for the fixes.
"""
from __future__ import annotations

import calendar
from contextlib import contextmanager
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.deps import get_current_user
from backend.app.main import app
from tests.conftest import _override_get_db
from backend.app.models import (
    Collaborator, CollaboratorCycleSummary, Cycle, Project, ProjectCyclePlan,
    TimesheetRecord, User, UserProjectAccess,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cycle(db, name, y, m, active=True):
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last), is_active=active)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _cycles(db, n, year=2025):
    return [_cycle(db, f"C{i + 1}", year, i + 1) for i in range(n)]


def _collab(db, name="Ana"):
    c = Collaborator(name=name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _project(db, pep, bh=None, bc=None, **kw):
    p = Project(pep_wbs=pep, name=f"Proj {pep}", budget_hours=bh, budget_cost=bc,
                status=kw.pop("status", "ativo"), **kw)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _rec(db, cycle, collab, pep, hours, rate=100.0, day=10, extra=0.0):
    r = TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep, pep_description=f"D {pep}",
        normal_hours=hours, extra_hours=extra, standby_hours=0.0,
        cost_per_hour=rate,
        normal_cost=round(hours * rate, 4),
        extra_cost=round(extra * rate, 4), standby_cost=0.0,
    )
    db.add(r)
    db.commit()
    return r


def _plan(db, project, cycle, hours, cost=None, phys=None):
    db.add(ProjectCyclePlan(project_id=project.id, cycle_id=cycle.id,
                            planned_hours=hours, planned_cost=cost, physical_pct=phys))
    db.commit()


def _restricted_user(db, *projects, username="restricted"):
    u = User(username=username, hashed_password="x", role="user")
    db.add(u)
    db.commit()
    db.refresh(u)
    for p in projects:
        db.add(UserProjectAccess(user_id=u.id, project_id=p.id))
    db.commit()
    return u


@contextmanager
def _as(user):
    saved = dict(app.dependency_overrides)
    try:
        app.dependency_overrides[get_db] = _override_get_db
        app.dependency_overrides[get_current_user] = lambda: user
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(saved)


def _fc(client, pep, **params):
    r = client.get("/api/v2/forecast", params={"pep_wbs": pep, **params})
    assert r.status_code == 200, r.text
    return r.json()


def _seed_four_peps(db):
    cyc = _cycle(db, "JAN", 2025, 1)
    col = _collab(db)
    projs = [_project(db, f"P{i}", 100.0, 10000.0) for i in range(1, 5)]
    for p in projs:
        _rec(db, cyc, col, p.pep_wbs, 8.0)
    return cyc, col, projs


# ---------------------------------------------------------------------------
# B3 — empty whitelist intersection must not mean "no filter"
# ---------------------------------------------------------------------------

class TestB3EmptyIntersection:

    @pytest.mark.parametrize("path", ["/api/v2/runway", "/api/v2/concentration"])
    def test_pep_outside_whitelist_returns_empty(self, db_session, path):
        _, _, projs = _seed_four_peps(db_session)
        user = _restricted_user(db_session, projs[0])
        with _as(user) as c:
            assert [x["pep_wbs"] for x in c.get(path).json()] == ["P1"]
            assert c.get(path, params={"pep_wbs": "P2"}).json() == []
            got = c.get(path, params={"pep_wbs": ["P1", "P2"]}).json()
            assert [x["pep_wbs"] for x in got] == ["P1"]

    @pytest.mark.parametrize("path", ["/api/v2/runway", "/api/v2/concentration"])
    def test_whitelist_with_deleted_projects_returns_empty(self, db_session, path):
        _seed_four_peps(db_session)
        user = User(username="orphan", hashed_password="x", role="user")
        db_session.add(user)
        db_session.commit()
        db_session.add(UserProjectAccess(user_id=user.id, project_id=987654))
        db_session.commit()
        with _as(user) as c:
            assert c.get(path).json() == []


# ---------------------------------------------------------------------------
# B4 — PEP ACL on every analytics endpoint
# ---------------------------------------------------------------------------

class TestB4Acl:

    def _two_peps(self, db):
        c1, c2 = _cycle(db, "JAN", 2025, 1), _cycle(db, "FEV", 2025, 2)
        col = _collab(db)
        p1 = _project(db, "P1", 100.0, 10000.0)
        p2 = _project(db, "P2", 100.0, 10000.0)
        _rec(db, c1, col, "P1", 5.0)
        _rec(db, c1, col, "P2", 7.0, day=11)
        _rec(db, c2, col, "P2", 9.0)
        return c1, c2, col, p1, p2

    def test_trends_restricted(self, db_session):
        _, _, _, p1, _ = self._two_peps(db_session)
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            body = c.get("/api/v2/trends").json()
            assert [(x["cycle_name"], x["total_hours"]) for x in body] == [("JAN", 5.0)]
            assert c.get("/api/v2/trends", params={"pep_wbs": "P2"}).json() == []

    def test_effort_restricted_counts_only_allowed_pep_hours(self, db_session):
        c1, c2, col, p1, _ = self._two_peps(db_session)
        # summary rows (all PEPs mixed) must not be used for a restricted user
        db_session.add(CollaboratorCycleSummary(
            collaborator_id=col.id, cycle_id=c1.id, normal_hours=12.0, total_hours=12.0,
            total_cost=1200.0))
        db_session.add(CollaboratorCycleSummary(
            collaborator_id=col.id, cycle_id=c2.id, normal_hours=9.0, total_hours=9.0,
            total_cost=900.0))
        db_session.commit()
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            body = c.get("/api/v2/effort").json()
            assert len(body) == 1 and body[0]["total_hours"] == 5.0
            assert c.get("/api/v2/effort", params={"pep_wbs": "P2"}).json() == []

    def test_effort_admin_unchanged(self, client, db_session):
        self._two_peps(db_session)
        body = client.get("/api/v2/effort").json()
        assert body[0]["total_hours"] == 21.0

    def test_filters_restricted(self, db_session):
        _, _, _, p1, _ = self._two_peps(db_session)
        other = _collab(db_session, "Only P2")
        _rec(db_session, _cycle(db_session, "MAR", 2025, 3), other, "P2", 3.0)
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            body = c.get("/api/v2/filters").json()
            assert [p["code"] for p in body["peps"]] == ["P1"]
            assert [x["name"] for x in body["collaborators"]] == ["Ana"]

    def test_dashboard_endpoints_restricted(self, db_session):
        _, _, _, p1, _ = self._two_peps(db_session)
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            tl = c.get("/api/dashboard/collaborator-timeline",
                       params={"collaborator_name": "Ana"}).json()
            assert [(x["cycle_name"], x["normal_hours"]) for x in tl] == [("JAN", 5.0)]
            assert c.get("/api/dashboard/collaborator-timeline",
                         params={"collaborator_name": "Ana", "pep_code": "P2"}).json() == []
            daily = c.get("/api/dashboard/collaborator-daily",
                          params={"collaborator_name": "Ana", "year": 2025, "month": 1}).json()
            assert sum(d["hours"] for d in daily) == 5.0
            csv_ = c.get("/api/dashboard/collaborator-export",
                         params={"collaborator_name": "Ana"}).text
            assert "P1" in csv_ and "P2" not in csv_

    @pytest.mark.parametrize("kind", ["simulate", "monte"])
    def test_per_project_endpoints_forbidden_outside_whitelist(self, db_session, kind):
        _, _, _, p1, p2 = self._two_peps(db_session)
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            def call(pid):
                if kind == "simulate":
                    return c.post(f"/api/v2/projects/{pid}/simulate", json={})
                return c.get(f"/api/v2/projects/{pid}/monte-carlo")
            assert call(p2.id).status_code == 403
            assert call(p1.id).status_code == 200

    def test_over_allocation_total_counts_all_peps(self, db_session):
        cyc = _cycle(db_session, "JAN", 2025, 1)
        col = _collab(db_session)
        p1 = _project(db_session, "P1")
        _project(db_session, "P2")
        _rec(db_session, cyc, col, "P1", 14.0)
        _rec(db_session, cyc, col, "P2", 12.0)
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            body = c.get("/api/v2/over-allocation", params={"threshold": 24}).json()
            assert len(body) == 1
            assert body[0]["total_hours"] == 26.0
            assert body[0]["pep_list"] == ["P1"]  # hidden PEP code is not disclosed

    def test_over_allocation_hidden_only_day_not_disclosed(self, db_session):
        cyc = _cycle(db_session, "JAN", 2025, 1)
        col = _collab(db_session)
        p1 = _project(db_session, "P1")
        _project(db_session, "P2")
        _rec(db_session, cyc, col, "P1", 2.0, day=3)
        _rec(db_session, cyc, col, "P2", 30.0, day=4)  # no visible hours that day
        user = _restricted_user(db_session, p1)
        with _as(user) as c:
            assert c.get("/api/v2/over-allocation", params={"threshold": 24}).json() == []


# ---------------------------------------------------------------------------
# B5 / B6 / B7 — Earned Schedule and idle cycles
# ---------------------------------------------------------------------------

def _plan_setup(db, n_plan=6, planned_cost=1000.0, bh=60.0, bc=6000.0):
    cycles = _cycles(db, n_plan)
    proj = _project(db, "ES-1", bh, bc)
    for c in cycles:
        _plan(db, proj, c, 10.0, planned_cost)
    return cycles, proj, _collab(db)


class TestB5EarnedSchedule:

    def test_es_uses_full_plan_curve(self, client, db_session):
        cycles, proj, col = _plan_setup(db_session)
        for c in cycles[:3]:
            _rec(db_session, c, col, "ES-1", 15.0)
        body = _fc(client, "ES-1")
        assert body["actual_time_cycles"] == 3
        assert body["es"] == pytest.approx(4.5)
        assert body["spi_t"] == pytest.approx(1.5)
        assert body["sv_t"] == pytest.approx(1.5)
        assert body["ieac_t"] == pytest.approx(6 / 1.5)

    def test_es_capped_at_planned_duration_when_plan_finished(self, client, db_session):
        cycles, proj, col = _plan_setup(db_session, n_plan=2, bh=20.0, bc=2000.0)
        more = [_cycle(db_session, f"X{i}", 2025, 3 + i) for i in range(2)]
        for c in cycles + more:
            _rec(db_session, c, col, "ES-1", 5.0)
        body = _fc(client, "ES-1")
        # 20h of 20h earned, plan lasted 2 cycles, 4 elapsed
        assert body["es"] == pytest.approx(2.0)
        assert body["spi_t"] == pytest.approx(0.5)


class TestB6IdleCycles:

    def test_idle_cycle_is_in_history(self, client, db_session):
        cycles, proj, col = _plan_setup(db_session)
        for i in (0, 1, 3):
            _rec(db_session, cycles[i], col, "ES-1", 15.0)
        body = _fc(client, "ES-1")
        hist = body["history"]
        assert [h["cycle_name"] for h in hist] == ["C1", "C2", "C3", "C4"]
        assert hist[2]["period_hours"] == 0.0
        assert hist[3]["cumulative_planned_cost"] == pytest.approx(4000.0)
        assert hist[3]["cumulative_hours"] == pytest.approx(45.0)
        assert body["actual_time_cycles"] == 4
        assert body["es"] == pytest.approx(4.5)

    def test_velocity_window_is_last_three_calendar_cycles(self, client, db_session):
        cycles, proj, col = _plan_setup(db_session)
        _rec(db_session, cycles[0], col, "ES-1", 30.0)
        _rec(db_session, cycles[3], col, "ES-1", 30.0)
        body = _fc(client, "ES-1")
        # last 3 cycles: C2 (0), C3 (0), C4 (30) -> 10 h/cycle
        assert body["avg_hours_per_cycle"] == pytest.approx(10.0)


class TestB7HoursOnlyPlan:

    def test_es_from_derived_planned_cost(self, client, db_session):
        cycles, proj, col = _plan_setup(db_session, planned_cost=None)
        for c in cycles[:3]:
            _rec(db_session, c, col, "ES-1", 15.0)
        body = _fc(client, "ES-1")
        assert body["es"] == pytest.approx(4.5)
        assert body["spi_t"] == pytest.approx(1.5)
        assert body["history"][-1]["cumulative_planned_cost"] == pytest.approx(3000.0)

    def test_es_from_hours_when_no_budget(self, client, db_session):
        cycles = _cycles(db_session, 4)
        proj = _project(db_session, "ES-2")
        for c in cycles:
            _plan(db_session, proj, c, 10.0)
        col = _collab(db_session)
        for c in cycles[:2]:
            _rec(db_session, c, col, "ES-2", 15.0)
        body = _fc(client, "ES-2")
        assert body["es"] == pytest.approx(3.0)
        assert body["spi_t"] == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# B8 — ceil of the unrounded estimate
# ---------------------------------------------------------------------------

class TestB8CompletionCycle:

    def test_completion_cycle_uses_ceil_of_unrounded(self, client, db_session):
        cycles = _cycles(db_session, 8)
        _project(db_session, "CC-1", 50.4, 5040.0)
        col = _collab(db_session)
        for c in cycles[:3]:
            _rec(db_session, c, col, "CC-1", 10.0)
        body = _fc(client, "CC-1")
        assert body["estimated_cycles_to_complete"] == pytest.approx(2.0)  # displayed
        assert body["estimated_completion_cycle"] == "C6"  # ceil(2.04) = 3 cycles


# ---------------------------------------------------------------------------
# B9 — TCPI when the budget is already spent
# ---------------------------------------------------------------------------

class TestB9Tcpi:

    def test_compute_tcpi_budget_spent(self):
        from backend.app.services.evm import compute_tcpi
        assert compute_tcpi(1000.0, 1000.0, 500.0) is None
        assert compute_tcpi(1000.0, 1200.0, 500.0) is None
        assert compute_tcpi(1000.0, 800.0, 400.0) == pytest.approx(3.0)

    def test_forecast_budget_consumed_state(self, client, db_session):
        cycles = _cycles(db_session, 1)
        _project(db_session, "T-1", 100.0, 1000.0)
        _rec(db_session, cycles[0], _collab(db_session), "T-1", 50.0, rate=24.0)
        body = _fc(client, "T-1")
        assert body["tcpi"] is None
        assert body["tcpi_status"] == "budget_consumed"
        assert body["tcpi_label"] == "Orçamento já consumido"
        assert body["tcpi_color"] == "danger"

    def test_forecast_scope_complete_state(self, client, db_session):
        cycles = _cycles(db_session, 1)
        _project(db_session, "T-2", 100.0, 1000.0)
        _rec(db_session, cycles[0], _collab(db_session), "T-2", 100.0, rate=8.0)
        body = _fc(client, "T-2")
        assert body["tcpi"] is None
        assert body["tcpi_status"] == "complete"

    def test_forecast_ok_state(self, client, db_session):
        cycles = _cycles(db_session, 1)
        _project(db_session, "T-3", 100.0, 1000.0)
        _rec(db_session, cycles[0], _collab(db_session), "T-3", 50.0, rate=8.0)
        body = _fc(client, "T-3")
        assert body["tcpi"] == pytest.approx((1000 - 500) / (1000 - 400), abs=1e-4)
        assert body["tcpi_status"] == "ok"


# ---------------------------------------------------------------------------
# B10 — EAC from unrounded CPI
# ---------------------------------------------------------------------------

class TestB10Eac:

    def test_compute_eac_from_ev(self):
        from backend.app.services.evm import compute_eac_from_ev
        assert compute_eac_from_ev(1000.0, 1000.0, 1100.0) == 1100.0
        assert compute_eac_from_ev(1000.0, None, 1100.0) is None
        assert compute_eac_from_ev(1000.0, 0.0, 0.0, default_to_bac=True) == 1000.0

    def test_forecast_eac_exact(self, client, db_session):
        cycles = _cycles(db_session, 1)
        _project(db_session, "E-1", 100.0, 1000.0)
        _rec(db_session, cycles[0], _collab(db_session), "E-1", 100.0, rate=11.0)
        body = _fc(client, "E-1")
        assert body["actual_cost"] == 1100.0
        assert body["eac"] == 1100.0
        assert body["vac"] == -100.0


# ---------------------------------------------------------------------------
# B11 — simulate
# ---------------------------------------------------------------------------

class TestB11Simulate:

    def test_no_budget_hours_is_422(self, client, db_session):
        cycles = _cycles(db_session, 1)
        p = _project(db_session, "S-0")
        _rec(db_session, cycles[0], _collab(db_session), "S-0", 10.0)
        r = client.post(f"/api/v2/projects/{p.id}/simulate", json={})
        assert r.status_code == 422
        assert "orçadas" in r.json()["detail"]

    def test_projected_eac_responds_to_scenario(self, client, db_session):
        cycles = _cycles(db_session, 3)
        p = _project(db_session, "S-1", 100.0, 10000.0)
        col = _collab(db_session)
        for c in cycles:
            _rec(db_session, c, col, "S-1", 10.0)  # 30h, R$ 3000
        base = client.post(f"/api/v2/projects/{p.id}/simulate", json={}).json()
        slow = client.post(f"/api/v2/projects/{p.id}/simulate",
                           json={"velocity_multiplier": 0.3}).json()
        extra = client.post(f"/api/v2/projects/{p.id}/simulate",
                            json={"extra_hours_per_cycle": 5}).json()
        assert base["projected_eac_cost"] == pytest.approx(10000.0)   # 7 x 10h staffed
        assert slow["projected_eac_cost"] == pytest.approx(10200.0)   # 24 x 3h staffed
        assert extra["projected_eac_cost"] == pytest.approx(10500.0)  # 5 x 15h staffed


# ---------------------------------------------------------------------------
# B12 — trends raw fallback cost deltas
# ---------------------------------------------------------------------------

class TestB12TrendsFallback:

    def test_cost_deltas_filled(self, client, db_session):
        c1, c2 = _cycle(db_session, "JAN", 2025, 1), _cycle(db_session, "FEV", 2025, 2)
        col = _collab(db_session)
        _rec(db_session, c1, col, "P1", 10.0, rate=100.0)
        _rec(db_session, c1, col, "P1", 0.0, rate=100.0, extra=2.0, day=12)
        _rec(db_session, c2, col, "P1", 20.0, rate=100.0)
        body = client.get("/api/v2/trends").json()
        assert body[1]["normal_cost_delta"] == pytest.approx(1000.0)
        assert body[1]["normal_cost_delta_pct"] == pytest.approx(100.0)
        assert body[1]["extra_cost_delta"] == pytest.approx(-200.0)
        assert body[1]["cost_delta"] == pytest.approx(800.0)


# ---------------------------------------------------------------------------
# B13 — input validation
# ---------------------------------------------------------------------------

_REVERSED = {"date_from": "2025-06-01", "date_to": "2025-01-01"}


class TestB13Validation:

    @pytest.mark.parametrize("path,extra", [
        ("/api/v2/portfolio", {}),
        ("/api/v2/effort", {}),
        ("/api/v2/trends", {}),
        ("/api/v2/forecast", {"pep_wbs": "X"}),
        ("/api/v2/allocation", {}),
        ("/api/v2/runway", {}),
        ("/api/v2/concentration", {}),
        ("/api/v2/over-allocation", {}),
        ("/api/dashboard/collaborator-timeline", {"collaborator_name": "Ana"}),
        ("/api/dashboard/collaborator-export", {"collaborator_name": "Ana"}),
    ])
    def test_reversed_range_is_422(self, client, path, extra):
        assert client.get(path, params={**extra, **_REVERSED}).status_code == 422

    def test_equal_dates_are_valid(self, client):
        r = client.get("/api/v2/trends", params={"date_from": "2025-01-01", "date_to": "2025-01-01"})
        assert r.status_code == 200

    def test_simulate_and_monte_carlo_reversed(self, client, db_session):
        p = _project(db_session, "V-1", 100.0, 1000.0)
        assert client.post(f"/api/v2/projects/{p.id}/simulate", json=_REVERSED).status_code == 422
        assert client.get(f"/api/v2/projects/{p.id}/monte-carlo", params=_REVERSED).status_code == 422

    @pytest.mark.parametrize("month", [0, 13, -1])
    def test_invalid_month_is_422(self, client, month):
        r = client.get("/api/dashboard/collaborator-daily",
                       params={"collaborator_name": "Ana", "year": 2025, "month": month})
        assert r.status_code == 422

    def test_invalid_year_is_422(self, client):
        r = client.get("/api/dashboard/collaborator-daily",
                       params={"collaborator_name": "Ana", "year": 0, "month": 1})
        assert r.status_code == 422

    def test_monte_carlo_always_has_histogram(self, client, db_session):
        cycles = _cycles(db_session, 3)
        col = _collab(db_session)
        p_insuf = _project(db_session, "MC-1", 100.0, 1000.0)
        _rec(db_session, cycles[0], col, "MC-1", 10.0)
        body = client.get(f"/api/v2/projects/{p_insuf.id}/monte-carlo").json()
        assert body["error"] == "insufficient_data"
        assert body["histogram"] == []

        p_done = _project(db_session, "MC-2", 20.0, 1000.0)
        for c in cycles[:2]:
            _rec(db_session, c, col, "MC-2", 15.0)
        body = client.get(f"/api/v2/projects/{p_done.id}/monte-carlo").json()
        assert body["error"] is None and body["p50"] == 0
        assert body["histogram"] == []


# ---------------------------------------------------------------------------
# B14 — closed project: CV and VAC consistent
# ---------------------------------------------------------------------------

class TestB14ClosedProject:

    def test_cv_equals_vac_when_closed(self, client, db_session):
        cycles = _cycles(db_session, 1)
        _project(db_session, "CL-1", 100.0, 1000.0, status="encerrado",
                 completion_date=date(2025, 1, 31))
        _rec(db_session, cycles[0], _collab(db_session), "CL-1", 20.0, rate=20.0)
        body = _fc(client, "CL-1")
        assert body["is_closed"] is True
        assert body["eac"] == pytest.approx(400.0)
        assert body["vac"] == pytest.approx(600.0)
        assert body["cv"] == pytest.approx(600.0)
        assert body["cpi"] == pytest.approx(2.5)
