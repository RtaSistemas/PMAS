from __future__ import annotations

from datetime import date

import pytest

from backend.app.models import Collaborator, Cycle, GlobalConfig, Project, TimesheetRecord


# ---------------------------------------------------------------------------
# Helpers (mirrors test_analytics.py conventions)
# ---------------------------------------------------------------------------

def _cycle(db, name, y, m):
    import calendar
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last))
    db.add(c); db.commit(); db.refresh(c)
    return c


def _collab(db, name):
    c = Collaborator(name=name); db.add(c); db.commit(); db.refresh(c)
    return c


def _project(db, pep, budget_h=None, budget_c=None, name=None):
    p = Project(pep_wbs=pep, name=name, budget_hours=budget_h, budget_cost=budget_c, status="ativo")
    db.add(p); db.commit(); db.refresh(p)
    return p


def _rec(db, cycle, collab, pep, desc="D", normal=8.0, extra=0.0, standby=0.0, day=10):
    r = TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep, pep_description=desc,
        normal_hours=normal, extra_hours=extra, standby_hours=standby,
        cost_per_hour=0.0,
    )
    db.add(r); db.commit()
    return r


def _rec_with_cost(db, cycle, collab, pep, desc="D", normal=8.0, cost_per_hour=10.0, day=10):
    r = TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep, pep_description=desc,
        normal_hours=normal, extra_hours=0.0, standby_hours=0.0,
        cost_per_hour=cost_per_hour,
    )
    db.add(r); db.commit()
    return r


# ===========================================================================
# /api/portfolio-runway
# ===========================================================================

class TestPortfolioRunway:

    def test_empty(self, client):
        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        assert result.json() == []

    def test_returns_200_with_valid_data(self, client, db_session):
        cy = _cycle(db_session, "RW1", 2026, 1)
        co = _collab(db_session, "Ana")
        _project(db_session, "P-RW1", budget_h=100.0, name="Runway Project")
        _rec(db_session, cy, co, "P-RW1", normal=40.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        assert len(data) == 1
        item = data[0]
        assert item["pep_wbs"] == "P-RW1"
        assert item["name"] == "Runway Project"
        assert item["budget_hours"] == 100.0
        assert item["consumed_hours"] == 40.0
        assert item["risk"] in ("ok", "warning", "critical", "overrun")

    def test_no_budget_pep_is_included_with_no_budget_risk(self, client, db_session):
        cy = _cycle(db_session, "RW2", 2026, 2)
        co = _collab(db_session, "Bob")
        # No project registered for this PEP
        _rec(db_session, cy, co, "P-NOBUDGET", normal=10.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-NOBUDGET"), None)
        assert item is not None
        assert item["risk"] == "no_budget"
        assert item["budget_hours"] is None
        assert item["pct_consumed"] is None

    def test_cycles_to_complete_computation(self, client, db_session):
        # Two cycles, each with 40h → avg=40h/cycle
        # Budget = 200h → consumed = 80h → remaining = 120h → cycles_to_complete = 3.0
        c1 = _cycle(db_session, "CC1", 2026, 1)
        c2 = _cycle(db_session, "CC2", 2026, 2)
        co = _collab(db_session, "Carlos")
        _project(db_session, "P-COMPL", budget_h=200.0, name="Completion Test")
        _rec(db_session, c1, co, "P-COMPL", normal=40.0, day=10)
        _rec(db_session, c2, co, "P-COMPL", normal=40.0, day=10)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-COMPL"), None)
        assert item is not None
        assert item["avg_hours_per_cycle"] == pytest.approx(40.0)
        assert item["consumed_hours"] == pytest.approx(80.0)
        assert item["cycles_to_complete"] == pytest.approx(3.0, abs=0.2)

    def test_overrun_risk(self, client, db_session):
        cy = _cycle(db_session, "OV1", 2026, 1)
        co = _collab(db_session, "Diana")
        _project(db_session, "P-OVER", budget_h=50.0)
        _rec(db_session, cy, co, "P-OVER", normal=60.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-OVER"), None)
        assert item is not None
        assert item["risk"] == "overrun"
        assert item["pct_consumed"] > 100.0

    def test_ok_risk(self, client, db_session):
        cy = _cycle(db_session, "OK1", 2026, 1)
        co = _collab(db_session, "Elena")
        _project(db_session, "P-OK", budget_h=200.0)
        _rec(db_session, cy, co, "P-OK", normal=10.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-OK"), None)
        assert item is not None
        assert item["risk"] == "ok"

    def test_filter_by_cycle_id(self, client, db_session):
        c1 = _cycle(db_session, "FRW1", 2026, 3)
        c2 = _cycle(db_session, "FRW2", 2026, 4)
        co = _collab(db_session, "Fabi")
        _rec(db_session, c1, co, "P-ONLY-C1", normal=8.0)
        _rec(db_session, c2, co, "P-ONLY-C2", normal=8.0)

        result = client.get(f"/api/portfolio-runway?cycle_id={c1.id}")
        assert result.status_code == 200
        codes = [r["pep_wbs"] for r in result.json()]
        assert "P-ONLY-C1" in codes
        assert "P-ONLY-C2" not in codes

    def test_filter_by_pep_wbs(self, client, db_session):
        cy = _cycle(db_session, "FRW3", 2026, 5)
        co = _collab(db_session, "Gio")
        _rec(db_session, cy, co, "P-TARGET", normal=8.0)
        _rec(db_session, cy, co, "P-OTHER",  normal=8.0)

        result = client.get("/api/portfolio-runway?pep_wbs=P-TARGET")
        assert result.status_code == 200
        data = result.json()
        assert all(r["pep_wbs"] == "P-TARGET" for r in data)

    def test_closed_cycle_data_included(self, client, db_session):
        # Closed cycles still have their data included in runway computation
        c = Cycle(name="CL-RW", start_date=date(2026, 6, 1), end_date=date(2026, 6, 30), is_closed=True)
        db_session.add(c); db_session.commit(); db_session.refresh(c)
        co = _collab(db_session, "Hector")
        _project(db_session, "P-CLOSED", budget_h=100.0)
        _rec(db_session, c, co, "P-CLOSED", normal=30.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        codes = [r["pep_wbs"] for r in result.json()]
        # Closed cycles should be included since they have valid timesheet data
        assert "P-CLOSED" in codes

    def test_cpi_computed_when_budget_cost_provided(self, client, db_session):
        cy = _cycle(db_session, "CPI1", 2026, 1)
        co = _collab(db_session, "Iris")
        _project(db_session, "P-CPI", budget_h=100.0, budget_c=1000.0)
        _rec_with_cost(db_session, cy, co, "P-CPI", normal=50.0, cost_per_hour=10.0)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-CPI"), None)
        assert item is not None
        # EV = (50/100)*1000 = 500; AC = 50*10 = 500; CPI = EV/AC = 1.0
        assert item["cpi"] == pytest.approx(1.0, abs=0.01)

    def test_estimated_completion_cycle_returned(self, client, db_session):
        # 2 cycles consumed 40h each → avg 40/cycle, budget 200 → 120h remaining → 3 cycles
        c1 = _cycle(db_session, "EC1", 2026, 1)
        c2 = _cycle(db_session, "EC2", 2026, 2)
        c3 = _cycle(db_session, "EC3", 2026, 3)
        c4 = _cycle(db_session, "EC4", 2026, 4)
        c5 = _cycle(db_session, "EC5", 2026, 5)
        co = _collab(db_session, "Juan")
        _project(db_session, "P-EST", budget_h=200.0)
        _rec(db_session, c1, co, "P-EST", normal=40.0, day=10)
        _rec(db_session, c2, co, "P-EST", normal=40.0, day=10)
        # remaining 120h / 40h per cycle = 3 cycles → should complete around cycle at index 2+3=5 (EC5)

        result = client.get("/api/portfolio-runway")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-EST"), None)
        assert item is not None
        assert item["estimated_completion_cycle"] is not None


# ===========================================================================
# /api/portfolio-concentration
# ===========================================================================

class TestPortfolioConcentration:

    def test_empty(self, client):
        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        assert result.json() == []

    def test_returns_200_with_valid_data(self, client, db_session):
        cy = _cycle(db_session, "CON1", 2026, 1)
        co = _collab(db_session, "Ana")
        _rec(db_session, cy, co, "P-CON1", normal=40.0)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        assert len(data) >= 1
        item = data[0]
        assert "pep_wbs" in item
        assert "top_contributors" in item
        assert "top1_pct" in item
        assert "risk" in item

    def test_high_risk_when_top1_above_60(self, client, db_session):
        cy = _cycle(db_session, "CON2", 2026, 2)
        co1 = _collab(db_session, "Alice")
        co2 = _collab(db_session, "Bob2")
        # Alice: 70h (70%), Bob: 30h (30%) → top1_pct = 70 → high risk
        _rec(db_session, cy, co1, "P-HIGH", normal=70.0, day=1)
        _rec(db_session, cy, co2, "P-HIGH", normal=30.0, day=2)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-HIGH"), None)
        assert item is not None
        assert item["risk"] == "high"
        assert item["top1_pct"] == pytest.approx(70.0, abs=0.1)

    def test_medium_risk_when_top1_between_40_and_60(self, client, db_session):
        cy = _cycle(db_session, "CON3", 2026, 3)
        co1 = _collab(db_session, "Charlie")
        co2 = _collab(db_session, "David")
        # Charlie: 50h (50%), David: 50h (50%) → top1_pct = 50 → medium risk
        _rec(db_session, cy, co1, "P-MED", normal=50.0, day=1)
        _rec(db_session, cy, co2, "P-MED", normal=50.0, day=2)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-MED"), None)
        assert item is not None
        assert item["risk"] == "medium"

    def test_low_risk_when_top1_below_40(self, client, db_session):
        cy = _cycle(db_session, "CON4", 2026, 4)
        co1 = _collab(db_session, "Emma")
        co2 = _collab(db_session, "Frank2")
        co3 = _collab(db_session, "Grace2")
        # Each has 33h (~33%) → top1_pct < 40 → low risk
        _rec(db_session, cy, co1, "P-LOW", normal=33.0, day=1)
        _rec(db_session, cy, co2, "P-LOW", normal=33.0, day=2)
        _rec(db_session, cy, co3, "P-LOW", normal=34.0, day=3)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-LOW"), None)
        assert item is not None
        assert item["risk"] == "low"

    def test_top_contributors_capped_at_3_plus_others(self, client, db_session):
        cy = _cycle(db_session, "CON5", 2026, 5)
        collabs = [_collab(db_session, f"Person{i}") for i in range(5)]
        for i, co in enumerate(collabs):
            _rec(db_session, cy, co, "P-MANY", normal=float(20 - i), day=i + 1)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-MANY"), None)
        assert item is not None
        # Should have 3 named contributors + 1 "Outros" entry
        assert len(item["top_contributors"]) == 4
        others_entry = next((c for c in item["top_contributors"] if c["name"].startswith("Outros")), None)
        assert others_entry is not None

    def test_up_to_3_contributors_no_others_entry(self, client, db_session):
        cy = _cycle(db_session, "CON6", 2026, 6)
        co1 = _collab(db_session, "H1")
        co2 = _collab(db_session, "H2")
        _rec(db_session, cy, co1, "P-FEW", normal=20.0, day=1)
        _rec(db_session, cy, co2, "P-FEW", normal=10.0, day=2)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-FEW"), None)
        assert item is not None
        assert len(item["top_contributors"]) == 2
        assert not any(c["name"].startswith("Outros") for c in item["top_contributors"])

    def test_percentages_sum_to_100(self, client, db_session):
        cy = _cycle(db_session, "CON7", 2026, 7)
        co1 = _collab(db_session, "I1")
        co2 = _collab(db_session, "I2")
        co3 = _collab(db_session, "I3")
        _rec(db_session, cy, co1, "P-PCT", normal=60.0, day=1)
        _rec(db_session, cy, co2, "P-PCT", normal=30.0, day=2)
        _rec(db_session, cy, co3, "P-PCT", normal=10.0, day=3)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-PCT"), None)
        assert item is not None
        total_pct = sum(c["pct"] for c in item["top_contributors"])
        assert total_pct == pytest.approx(100.0, abs=1.0)

    def test_filter_by_cycle_id(self, client, db_session):
        c1 = _cycle(db_session, "FCON1", 2026, 8)
        c2 = _cycle(db_session, "FCON2", 2026, 9)
        co = _collab(db_session, "J1")
        _rec(db_session, c1, co, "P-FCON1", normal=8.0)
        _rec(db_session, c2, co, "P-FCON2", normal=8.0)

        result = client.get(f"/api/portfolio-concentration?cycle_id={c1.id}")
        assert result.status_code == 200
        codes = [r["pep_wbs"] for r in result.json()]
        assert "P-FCON1" in codes
        assert "P-FCON2" not in codes

    def test_filter_by_pep_description(self, client, db_session):
        cy = _cycle(db_session, "FCON3", 2026, 10)
        co = _collab(db_session, "K1")
        _rec(db_session, cy, co, "P-D1", desc="TargetDesc", normal=8.0, day=1)
        _rec(db_session, cy, co, "P-D2", desc="OtherDesc",  normal=8.0, day=2)

        result = client.get("/api/portfolio-concentration?pep_description=TargetDesc")
        assert result.status_code == 200
        codes = [r["pep_wbs"] for r in result.json()]
        assert "P-D1" in codes
        assert "P-D2" not in codes

    def test_project_name_included_when_registered(self, client, db_session):
        cy = _cycle(db_session, "CON8", 2026, 11)
        co = _collab(db_session, "L1")
        _project(db_session, "P-NAMED", name="Named Project")
        _rec(db_session, cy, co, "P-NAMED", normal=10.0)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-NAMED"), None)
        assert item is not None
        assert item["name"] == "Named Project"

    def test_total_hours_correct(self, client, db_session):
        cy = _cycle(db_session, "CON9", 2026, 12)
        co1 = _collab(db_session, "M1")
        co2 = _collab(db_session, "M2")
        _rec(db_session, cy, co1, "P-TOTAL", normal=25.0, day=1)
        _rec(db_session, cy, co2, "P-TOTAL", normal=15.0, day=2)

        result = client.get("/api/portfolio-concentration")
        assert result.status_code == 200
        data = result.json()
        item = next((x for x in data if x["pep_wbs"] == "P-TOTAL"), None)
        assert item is not None
        assert item["total_hours"] == pytest.approx(40.0)
