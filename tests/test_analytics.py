from __future__ import annotations

from datetime import date

from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord


def _cycle(db, name, y, m):
    import calendar
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last), is_quarantine=False)
    db.add(c); db.commit(); db.refresh(c)
    return c


def _collab(db, name):
    c = Collaborator(name=name); db.add(c); db.commit(); db.refresh(c)
    return c


def _project(db, pep, budget=None, name=None):
    p = Project(pep_wbs=pep, name=name, budget_hours=budget, status="ativo")
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


# ===========================================================================
# /api/portfolio-health
# ===========================================================================

class TestPortfolioHealth:
    def test_empty(self, client):
        assert client.get("/api/portfolio-health").json() == []

    def test_returns_pep_with_hours(self, client, db_session):
        cy = _cycle(db_session, "C1", 2026, 1)
        co = _collab(db_session, "Ana")
        _rec(db_session, cy, co, "PEP-A", normal=16.0)
        result = client.get("/api/portfolio-health").json()
        assert any(r["pep_wbs"] == "PEP-A" for r in result)

    def test_consumed_hours_sum(self, client, db_session):
        cy = _cycle(db_session, "C2", 2026, 2)
        co = _collab(db_session, "Bia")
        _rec(db_session, cy, co, "PEP-B", normal=8.0, extra=0.0,  standby=0.0, day=1)
        _rec(db_session, cy, co, "PEP-B", normal=0.0, extra=4.0,  standby=0.0, day=2)
        _rec(db_session, cy, co, "PEP-B", normal=0.0, extra=0.0,  standby=2.0, day=3)
        result = client.get("/api/portfolio-health").json()
        pep = next(r for r in result if r["pep_wbs"] == "PEP-B")
        assert pep["consumed_hours"] == 14.0

    def test_registered_flag_true(self, client, db_session):
        cy = _cycle(db_session, "C3", 2026, 3)
        co = _collab(db_session, "Carlos")
        _project(db_session, "REG-001", budget=100.0, name="Projeto X")
        _rec(db_session, cy, co, "REG-001")
        result = client.get("/api/portfolio-health").json()
        pep = next(r for r in result if r["pep_wbs"] == "REG-001")
        assert pep["is_registered"] is True
        assert pep["budget_hours"] == 100.0
        assert pep["name"] == "Projeto X"

    def test_unregistered_flag_false(self, client, db_session):
        cy = _cycle(db_session, "C4", 2026, 4)
        co = _collab(db_session, "Diana")
        _rec(db_session, cy, co, "ORPAN-999")
        result = client.get("/api/portfolio-health").json()
        pep = next(r for r in result if r["pep_wbs"] == "ORPAN-999")
        assert pep["is_registered"] is False
        assert pep["budget_hours"] is None

    def test_filter_by_cycle_id(self, client, db_session):
        c1 = _cycle(db_session, "FC1", 2026, 5)
        c2 = _cycle(db_session, "FC2", 2026, 6)
        co = _collab(db_session, "Edu")
        _rec(db_session, c1, co, "ONLY-C1")
        _rec(db_session, c2, co, "ONLY-C2")
        result = client.get(f"/api/portfolio-health?cycle_id={c1.id}").json()
        codes = [r["pep_wbs"] for r in result]
        assert "ONLY-C1" in codes
        assert "ONLY-C2" not in codes

    def test_filter_by_pep_wbs(self, client, db_session):
        cy = _cycle(db_session, "FP1", 2026, 7)
        co = _collab(db_session, "Fabi")
        _rec(db_session, cy, co, "TARGET")
        _rec(db_session, cy, co, "OTHER")
        result = client.get("/api/portfolio-health?pep_wbs=TARGET").json()
        assert all(r["pep_wbs"] == "TARGET" for r in result)

    def test_sorted_by_consumed_hours_desc(self, client, db_session):
        cy = _cycle(db_session, "SORT", 2026, 8)
        co = _collab(db_session, "Gio")
        _rec(db_session, cy, co, "LOW",  normal=2.0, day=1)
        _rec(db_session, cy, co, "HIGH", normal=20.0, day=2)
        result = client.get("/api/portfolio-health").json()
        codes = [r["pep_wbs"] for r in result]
        assert codes.index("HIGH") < codes.index("LOW")

    def test_excludes_records_without_pep(self, client, db_session):
        cy = _cycle(db_session, "NOPEP", 2026, 9)
        co = _collab(db_session, "Hel")
        r = TimesheetRecord(
            collaborator_id=co.id, cycle_id=cy.id,
            record_date=date(2026, 9, 10),
            pep_wbs=None, pep_description=None,
            normal_hours=8.0, extra_hours=0.0, standby_hours=0.0, cost_per_hour=0.0,
        )
        db_session.add(r); db_session.commit()
        result = client.get("/api/portfolio-health").json()
        assert all(r["pep_wbs"] is not None for r in result)


# ===========================================================================
# /api/trends
# ===========================================================================

class TestTrends:
    def test_empty(self, client):
        assert client.get("/api/trends").json() == []

    def test_returns_cycles_with_hours(self, client, db_session):
        cy = _cycle(db_session, "T1", 2026, 1)
        co = _collab(db_session, "Ivan")
        _rec(db_session, cy, co, "P1", normal=8.0)
        result = client.get("/api/trends").json()
        assert any(r["cycle_name"] == "T1" for r in result)

    def test_aggregates_all_hour_types(self, client, db_session):
        cy = _cycle(db_session, "T2", 2026, 2)
        co = _collab(db_session, "Julia")
        _rec(db_session, cy, co, "P2", normal=8.0, extra=0.0,  standby=0.0, day=1)
        _rec(db_session, cy, co, "P2", normal=0.0, extra=4.0,  standby=0.0, day=2)
        _rec(db_session, cy, co, "P2", normal=0.0, extra=0.0,  standby=2.0, day=3)
        result = client.get("/api/trends").json()
        t = next(r for r in result if r["cycle_name"] == "T2")
        assert t["normal_hours"] == 8.0
        assert t["extra_hours"]  == 4.0
        assert t["standby_hours"] == 2.0

    def test_chronological_order(self, client, db_session):
        c1 = _cycle(db_session, "Jan/2026", 2026, 1)
        c2 = _cycle(db_session, "Mar/2026", 2026, 3)
        c3 = _cycle(db_session, "Feb/2026", 2026, 2)  # inserted out of order
        co = _collab(db_session, "Karl")
        for cy in [c1, c2, c3]:
            _rec(db_session, cy, co, "P3")
        result = client.get("/api/trends").json()
        names = [r["cycle_name"] for r in result]
        assert names == ["Jan/2026", "Feb/2026", "Mar/2026"]

    def test_excludes_quarantine_cycles(self, client, db_session):
        regular    = _cycle(db_session, "Regular", 2026, 1)
        quarantine = Cycle(
            name="Quarentena - Jan/2099",
            start_date=date(2099, 1, 1), end_date=date(2099, 1, 31), is_quarantine=True,
        )
        db_session.add(quarantine); db_session.commit()
        co = _collab(db_session, "Laura")
        _rec(db_session, regular, co, "P4")
        r = TimesheetRecord(
            collaborator_id=co.id, cycle_id=quarantine.id,
            record_date=date(2099, 1, 10), pep_wbs="P4", pep_description="D",
            normal_hours=8.0, extra_hours=0.0, standby_hours=0.0, cost_per_hour=0.0,
        )
        db_session.add(r); db_session.commit()
        result = client.get("/api/trends").json()
        names = [r["cycle_name"] for r in result]
        assert "Regular" in names
        assert "Quarentena - Jan/2099" not in names

    def test_filter_by_pep_wbs(self, client, db_session):
        cy = _cycle(db_session, "FPEP", 2026, 4)
        co = _collab(db_session, "Marcos")
        _rec(db_session, cy, co, "WANT",   normal=10.0, day=1)
        _rec(db_session, cy, co, "IGNORE", normal=5.0,  day=2)
        result = client.get("/api/trends?pep_wbs=WANT").json()
        assert len(result) == 1
        assert result[0]["normal_hours"] == 10.0

    def test_multiple_cycles_aggregated_separately(self, client, db_session):
        c1 = _cycle(db_session, "MA1", 2026, 5)
        c2 = _cycle(db_session, "MA2", 2026, 6)
        co = _collab(db_session, "Nina")
        _rec(db_session, c1, co, "P5", normal=6.0)
        _rec(db_session, c2, co, "P5", normal=9.0)
        result = client.get("/api/trends").json()
        names_to_hours = {r["cycle_name"]: r["normal_hours"] for r in result}
        assert names_to_hours["MA1"] == 6.0
        assert names_to_hours["MA2"] == 9.0


# ===========================================================================
# /api/dashboard/pep-radar
# ===========================================================================

class TestPepRadar:
    def test_empty(self, client):
        assert client.get("/api/dashboard/pep-radar").json() == []

    def test_returns_hours_and_cost_per_pep_description(self, client, db_session):
        cy = _cycle(db_session, "R1", 2026, 1)
        co = _collab(db_session, "Ana")
        _rec(db_session, cy, co, "P1", desc="Alpha", normal=8.0)
        _rec(db_session, cy, co, "P2", desc="Beta",  normal=4.0)
        result = client.get("/api/dashboard/pep-radar").json()
        descs = {r["pep_description"] for r in result}
        assert descs == {"Alpha", "Beta"}

    def test_sorted_desc_by_hours(self, client, db_session):
        cy = _cycle(db_session, "R2", 2026, 2)
        co = _collab(db_session, "Bob")
        _rec(db_session, cy, co, "P1", desc="Low",  normal=2.0)
        _rec(db_session, cy, co, "P2", desc="High", normal=10.0)
        result = client.get("/api/dashboard/pep-radar").json()
        assert result[0]["pep_description"] == "High"
        assert result[1]["pep_description"] == "Low"

    def test_excludes_records_without_pep_description(self, client, db_session):
        cy = _cycle(db_session, "R3", 2026, 3)
        co = _collab(db_session, "Carl")
        r = TimesheetRecord(
            collaborator_id=co.id, cycle_id=cy.id,
            record_date=date(2026, 3, 5),
            pep_wbs=None, pep_description=None,
            normal_hours=8.0, extra_hours=0.0, standby_hours=0.0, cost_per_hour=0.0,
        )
        db_session.add(r); db_session.commit()
        assert client.get("/api/dashboard/pep-radar").json() == []

    def test_filter_by_cycle_id(self, client, db_session):
        c1 = _cycle(db_session, "R4a", 2026, 4)
        c2 = _cycle(db_session, "R4b", 2026, 5)
        co = _collab(db_session, "Diana")
        _rec(db_session, c1, co, "P1", desc="Want",   normal=8.0)
        _rec(db_session, c2, co, "P2", desc="Ignore", normal=5.0)
        result = client.get(f"/api/dashboard/pep-radar?cycle_id={c1.id}").json()
        assert len(result) == 1
        assert result[0]["pep_description"] == "Want"

    def test_limits_to_12_peps(self, client, db_session):
        cy = _cycle(db_session, "R5", 2026, 6)
        co = _collab(db_session, "Eve")
        for i in range(15):
            _rec(db_session, cy, co, f"P{i}", desc=f"Desc{i}", normal=float(i + 1))
        result = client.get("/api/dashboard/pep-radar").json()
        assert len(result) == 12
