"""Audit cycle 3 (leftovers): inactive cycles in runway/concentration, ceil float noise."""
from __future__ import annotations

import calendar
from datetime import date

from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord


def _cycle(db, name, y, m, active=True):
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last), is_active=active)
    db.add(c); db.commit(); db.refresh(c)
    return c


def _rec(db, cycle, collab, pep, hours):
    db.add(TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id, record_date=cycle.start_date,
        pep_wbs=pep, pep_description="D", normal_hours=hours, extra_hours=0.0,
        standby_hours=0.0, cost_per_hour=10.0, normal_cost=hours * 10.0,
        extra_cost=0.0, standby_cost=0.0,
    ))
    db.commit()


def _setup(db, budget=100.0):
    col = Collaborator(name="Ana"); db.add(col)
    db.add(Project(pep_wbs="P-1", name="P1", budget_hours=budget, budget_cost=budget * 10, status="em_andamento"))
    db.commit(); db.refresh(col)
    return col


def test_runway_excludes_inactive_cycles(client, db_session, clean_db):
    col = _setup(db_session)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    cq = _cycle(db_session, "QUAR/2025", 2025, 2, active=False)
    _rec(db_session, c1, col, "P-1", 10.0)
    _rec(db_session, cq, col, "P-1", 50.0)
    row = client.get("/api/v2/runway").json()[0]
    assert row["consumed_hours"] == 10.0


def test_concentration_excludes_inactive_cycles(client, db_session, clean_db):
    col = _setup(db_session)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    cq = _cycle(db_session, "QUAR/2025", 2025, 2, active=False)
    _rec(db_session, c1, col, "P-1", 10.0)
    _rec(db_session, cq, col, "P-1", 50.0)
    rows = client.get("/api/v2/concentration").json()
    assert sum(r["total_hours"] for r in rows) == 10.0


def test_simulate_ceil_ignores_float_noise(client, db_session, clean_db):
    col = _setup(db_session, budget=21.7)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    _rec(db_session, c1, col, "P-1", 0.7)
    pid = db_session.query(Project).first().id
    body = client.post(f"/api/v2/projects/{pid}/simulate", json={}).json()
    assert body["cycles_to_complete"] == 30


def test_runway_ceil_ignores_float_noise(client, db_session, clean_db):
    col = _setup(db_session, budget=21.7)
    cycles = [_cycle(db_session, f"C{i:02d}", 2025 + i // 12, i % 12 + 1) for i in range(33)]
    _rec(db_session, cycles[0], col, "P-1", 0.7)
    row = client.get("/api/v2/runway").json()[0]
    assert row["estimated_completion_cycle"] == "C30"


def test_list_routes_accept_both_slash_forms(client, clean_db):
    for url in ("/api/my/notifications", "/api/my/notifications/",
                "/api/project-alerts", "/api/project-alerts/"):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 200, (url, r.status_code)


def test_alias_routes_hidden_from_schema(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/my/notifications" not in paths
    assert "/api/project-alerts" not in paths
    assert "/api/my/notifications/" in paths
