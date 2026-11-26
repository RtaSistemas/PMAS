"""Product decision: EVM of the whole project; one date-filter rule elsewhere.

(a) forecast, simulate and monte-carlo ignore date_from/date_to (audit B1).
(b) every other analytics endpoint reads the range by the record date (audit B2).
"""
from __future__ import annotations

from datetime import date

from backend.app.models import TimesheetRecord
from backend.app.services.summaries import backfill_summaries
from tests.test_audit_analytics import (
    _collab, _cycle, _plan, _project,
)

PEP = "60IT-DF-01"
RANGE = {"date_from": "2026-02-08", "date_to": "2026-04-30"}
# (month, day, hours): the range cuts through the middle of February
_ROWS = [(1, 10, 6.0), (2, 5, 8.0), (2, 10, 8.0), (3, 10, 10.0), (4, 10, 12.0), (5, 10, 4.0)]
IN_RANGE = 8.0 + 10.0 + 12.0   # 30
WHOLE = sum(h for _, _, h in _ROWS)


def _seed(db, rate=100.0):
    cycles = {m: _cycle(db, f"M{m}", 2026, m) for m in range(1, 6)}
    ana = _collab(db)
    proj = _project(db, PEP, bh=200.0, bc=20000.0)
    for m, d, h in _ROWS:
        db.add(TimesheetRecord(
            collaborator_id=ana.id, cycle_id=cycles[m].id, record_date=date(2026, m, d),
            pep_wbs=PEP, pep_description="D", normal_hours=h, extra_hours=0.0,
            standby_hours=0.0, cost_per_hour=rate, normal_cost=h * rate,
            extra_cost=0.0, standby_cost=0.0))
    db.commit()
    for m in (1, 2, 3, 4, 5):
        _plan(db, proj, cycles[m], 20.0, 2000.0)
    backfill_summaries(db)
    return proj, ana


def test_totals_agree_across_endpoints_for_a_mid_cycle_range(client, db_session):
    _, ana = _seed(db_session)
    p = {**RANGE, "pep_wbs": PEP}
    portfolio = client.get("/api/v2/portfolio", params=p).json()
    effort = client.get("/api/v2/effort", params=p).json()
    trends = client.get("/api/v2/trends", params=p).json()
    runway = client.get("/api/v2/runway", params=p).json()
    alloc = client.get("/api/v2/allocation", params=p).json()
    conc = client.get("/api/v2/concentration", params=p).json()
    timeline = client.get("/api/dashboard/collaborator-timeline",
                          params={**RANGE, "collaborator_name": ana.name, "pep_code": PEP}).json()

    totals = {
        "portfolio": sum(r["total_hours"] for r in portfolio),
        "effort": sum(r["total_hours"] for r in effort),
        "trends": sum(r["total_hours"] for r in trends),
        "runway": sum(r["consumed_hours"] for r in runway),
        "allocation": sum(r["total_hours"] for r in alloc),
        "concentration": sum(r["total_hours"] for r in conc),
        "dashboard": sum(r["normal_hours"] + r["extra_hours"] + r["standby_hours"] for r in timeline),
    }
    assert totals == {k: IN_RANGE for k in totals}, totals
    # cost follows the same rule
    assert portfolio[0]["total_cost"] == IN_RANGE * 100.0
    assert sum(r["total_cost"] for r in effort) == IN_RANGE * 100.0
    assert sum(r["actual_cost"] for r in trends) == IN_RANGE * 100.0


def test_single_bound_ranges_use_the_record_date(client, db_session):
    _seed(db_session)
    only_from = client.get("/api/v2/portfolio", params={"date_from": "2026-02-08", "pep_wbs": PEP}).json()
    assert only_from[0]["total_hours"] == 8.0 + 10.0 + 12.0 + 4.0
    only_to = client.get("/api/v2/effort", params={"date_to": "2026-02-10"}).json()
    assert sum(r["total_hours"] for r in only_to) == 6.0 + 8.0 + 8.0   # inclusive bound
    trends = client.get("/api/v2/trends", params={"date_from": "2026-02-10", "date_to": "2026-02-10"}).json()
    assert [t["total_hours"] for t in trends] == [8.0]


def test_unfiltered_numbers_are_unchanged(client, db_session):
    _seed(db_session)
    assert client.get("/api/v2/portfolio").json()[0]["total_hours"] == WHOLE
    assert sum(r["total_hours"] for r in client.get("/api/v2/effort").json()) == WHOLE
    assert sum(r["total_hours"] for r in client.get("/api/v2/trends").json()) == WHOLE


def test_forecast_ignores_the_date_range(client, db_session):
    _seed(db_session)
    base = client.get("/api/v2/forecast", params={"pep_wbs": PEP}).json()
    filt = client.get("/api/v2/forecast", params={"pep_wbs": PEP, **RANGE}).json()
    assert filt == base
    assert base["spi"] is not None


def test_simulate_ignores_the_date_range(client, db_session):
    proj, _ = _seed(db_session)
    url = f"/api/v2/projects/{proj.id}/simulate"
    body = {"velocity_multiplier": 1.0, "extra_hours": 0}
    base = client.post(url, json=body)
    filt = client.post(url, json={**body, **RANGE})
    assert base.status_code == 200, base.text
    assert filt.json() == base.json()


def test_monte_carlo_ignores_the_date_range(client, db_session):
    proj, _ = _seed(db_session)
    url = f"/api/v2/projects/{proj.id}/monte-carlo"
    base = client.get(url, params={"seed": 7})
    filt = client.get(url, params={"seed": 7, **RANGE})
    assert base.status_code == 200, base.text
    assert filt.json() == base.json()


def test_openapi_documents_the_ignored_range(client):
    spec = client.get("/openapi.json").json()
    params = spec["paths"]["/api/v2/projects/{project_id}/monte-carlo"]["get"]["parameters"]
    texts = [p.get("description", "") for p in params if p["name"] in ("date_from", "date_to")]
    assert texts and all("ignored" in t.lower() for t in texts)
    assert "ignored" in spec["paths"]["/api/v2/forecast"]["get"]["description"].lower()
