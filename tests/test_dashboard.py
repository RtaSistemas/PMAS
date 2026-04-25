from __future__ import annotations

from datetime import date

from backend.app.models import Collaborator, Cycle, TimesheetRecord


def _add_record(db, cycle, collab, pep="PEP-X", desc="Desc X",
                normal=8.0, extra=0.0, standby=0.0, day=15):
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=date(2026, 1, day),
        pep_wbs=pep,
        pep_description=desc,
        normal_hours=normal,
        extra_hours=extra,
        standby_hours=standby,
    )
    db.add(r)
    db.commit()
    return r


class TestDashboardAll:
    def test_empty_base(self, client):
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        d = r.json()
        assert d["data"] == []
        assert d["cycle"]["id"] is None
        assert d["cycle"]["name"] == "Toda a base"
        assert d["budget_vs_actual"] == []

    def test_aggregates_all_cycles(self, client, db_session, sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator, normal=6.0, day=10)
        _add_record(db_session, sample_cycle, sample_collaborator, normal=4.0, day=11)
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 1
        assert data[0]["normal_hours"] == 10.0

    def test_filter_by_pep_code(self, client, db_session, sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator, pep="A-001", normal=8.0, day=1)
        _add_record(db_session, sample_cycle, sample_collaborator, pep="B-002", normal=5.0, day=2)
        r = client.get("/api/dashboard?pep_code=A-001")
        data = r.json()["data"]
        assert len(data) == 1
        assert data[0]["normal_hours"] == 8.0

    def test_budget_vs_actual_in_all(self, client, db_session, sample_cycle,
                                     sample_collaborator, sample_project):
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep=sample_project.pep_wbs, normal=80.0)
        r = client.get(f"/api/dashboard?pep_code={sample_project.pep_wbs}")
        bva = r.json()["budget_vs_actual"]
        assert len(bva) == 1
        assert bva[0]["budget_hours"] == sample_project.budget_hours
        assert bva[0]["actual_hours"] == 80.0


class TestDashboardByCycle:
    def test_cycle_not_found(self, client):
        assert client.get("/api/dashboard/99999").status_code == 404

    def test_aggregates_hours_for_cycle(self, client, db_session,
                                        sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator, normal=5.0, extra=0.0, day=10)
        _add_record(db_session, sample_cycle, sample_collaborator, normal=0.0, extra=3.0, day=11)
        r = client.get(f"/api/dashboard/{sample_cycle.id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 1
        assert data[0]["normal_hours"] == 5.0
        assert data[0]["extra_hours"] == 3.0

    def test_returns_cycle_metadata(self, client, sample_cycle):
        r = client.get(f"/api/dashboard/{sample_cycle.id}")
        cycle = r.json()["cycle"]
        assert cycle["id"] == sample_cycle.id
        assert cycle["name"] == sample_cycle.name
        assert cycle["start_date"] == "2026-01-01"
        assert cycle["end_date"] == "2026-01-31"

    def test_breakdown_populated(self, client, db_session, sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep="P-001", desc="Desc 1", normal=4.0, day=5)
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep="P-002", desc="Desc 2", normal=6.0, day=6)
        r = client.get(f"/api/dashboard/{sample_cycle.id}")
        breakdown = r.json()["breakdown"]
        assert len(breakdown) >= 2
        peps = [b["pep_code"] for b in breakdown]
        assert "P-001" in peps
        assert "P-002" in peps

    def test_filter_by_collaborator(self, client, db_session, sample_cycle):
        c1 = Collaborator(name="Collab Um"); db_session.add(c1); db_session.commit()
        c2 = Collaborator(name="Collab Dois"); db_session.add(c2); db_session.commit()
        _add_record(db_session, sample_cycle, c1, normal=8.0, day=10)
        _add_record(db_session, sample_cycle, c2, normal=4.0, day=11)
        r = client.get(f"/api/dashboard/{sample_cycle.id}?collaborator_id={c1.id}")
        data = r.json()["data"]
        assert len(data) == 1
        assert data[0]["collaborator"] == "Collab Um"

    def test_budget_vs_actual_by_cycle(self, client, db_session,
                                       sample_cycle, sample_collaborator, sample_project):
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep=sample_project.pep_wbs, normal=40.0, day=5)
        r = client.get(f"/api/dashboard/{sample_cycle.id}")
        bva = r.json()["budget_vs_actual"]
        assert len(bva) == 1
        assert bva[0]["actual_hours"] == 40.0
        assert bva[0]["budget_hours"] == 160.0

    def test_quarantine_cycle_flagged(self, client, db_session):
        qcycle = Cycle(
            name="Quarentena - Jan/2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            is_quarantine=True,
        )
        db_session.add(qcycle)
        db_session.commit()
        r = client.get(f"/api/dashboard/{qcycle.id}")
        assert r.json()["cycle"]["is_quarantine"] is True

    def test_isolates_records_by_cycle(self, client, db_session, sample_collaborator):
        c1 = Cycle(name="C1", start_date=date(2026, 2, 1),
                   end_date=date(2026, 2, 28), is_quarantine=False)
        c2 = Cycle(name="C2", start_date=date(2026, 3, 1),
                   end_date=date(2026, 3, 31), is_quarantine=False)
        db_session.add_all([c1, c2]); db_session.commit()
        _add_record(db_session, c1, sample_collaborator, normal=10.0,
                    day=1)  # day is in Jan but cycle fixture forces the cycle
        r = client.get(f"/api/dashboard/{c2.id}")
        assert r.json()["data"] == []
