from __future__ import annotations

from datetime import date

from backend.app.models import Collaborator, Cycle, TimesheetRecord


def _add_record(db, cycle, collab, pep="P-X", desc="Desc X", day=10):
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=date(2026, 1, day),
        pep_wbs=pep,
        pep_description=desc,
        normal_hours=8.0,
        extra_hours=0.0,
        standby_hours=0.0,
    )
    db.add(r)
    db.commit()
    return r


class TestCollaborators:
    def test_empty(self, client):
        assert client.get("/api/collaborators").json() == []

    def test_returns_collaborators_with_records(self, client, db_session,
                                                sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator)
        result = client.get("/api/collaborators").json()
        assert any(c["name"] == sample_collaborator.name for c in result)

    def test_no_records_no_collaborator(self, client, db_session):
        c = Collaborator(name="SemRegistros")
        db_session.add(c); db_session.commit()
        result = client.get("/api/collaborators").json()
        assert not any(x["name"] == "SemRegistros" for x in result)

    def test_distinct_per_collaborator(self, client, db_session,
                                       sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator, day=10)
        _add_record(db_session, sample_cycle, sample_collaborator, day=11)
        result = client.get("/api/collaborators").json()
        names = [x["name"] for x in result]
        assert names.count(sample_collaborator.name) == 1

    def test_filter_by_cycle(self, client, db_session, sample_collaborator):
        c1 = Cycle(name="C1", start_date=date(2026, 2, 1),
                   end_date=date(2026, 2, 28), is_quarantine=False)
        c2 = Cycle(name="C2", start_date=date(2026, 3, 1),
                   end_date=date(2026, 3, 31), is_quarantine=False)
        db_session.add_all([c1, c2]); db_session.commit()

        other = Collaborator(name="Outro"); db_session.add(other); db_session.commit()
        _add_record(db_session, c1, sample_collaborator)
        _add_record(db_session, c2, other)

        result = client.get(f"/api/collaborators?cycle_id={c1.id}").json()
        names = [x["name"] for x in result]
        assert sample_collaborator.name in names
        assert "Outro" not in names

    def test_filter_by_pep_code(self, client, db_session, sample_cycle, sample_collaborator):
        other = Collaborator(name="OutroPEP"); db_session.add(other); db_session.commit()
        _add_record(db_session, sample_cycle, sample_collaborator, pep="PEP-A")
        _add_record(db_session, sample_cycle, other, pep="PEP-B")

        result = client.get("/api/collaborators?pep_code=PEP-A").json()
        names = [x["name"] for x in result]
        assert sample_collaborator.name in names
        assert "OutroPEP" not in names

    def test_filter_by_pep_description(self, client, db_session,
                                        sample_cycle, sample_collaborator):
        other = Collaborator(name="OutraDesc"); db_session.add(other); db_session.commit()
        _add_record(db_session, sample_cycle, sample_collaborator, desc="Alpha")
        _add_record(db_session, sample_cycle, other, desc="Beta")

        result = client.get("/api/collaborators?pep_description=Alpha").json()
        names = [x["name"] for x in result]
        assert sample_collaborator.name in names
        assert "OutraDesc" not in names


class TestPeps:
    def test_empty(self, client):
        assert client.get("/api/peps").json() == []

    def test_returns_peps_with_records(self, client, db_session,
                                       sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator, pep="PEP-VIS")
        result = client.get("/api/peps").json()
        codes = [p["code"] for p in result]
        assert "PEP-VIS" in codes

    def test_groups_multiple_descriptions(self, client, db_session,
                                          sample_cycle, sample_collaborator):
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep="MULTI", desc="Desc 1", day=1)
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep="MULTI", desc="Desc 2", day=2)
        result = client.get("/api/peps").json()
        pep = next(p for p in result if p["code"] == "MULTI")
        assert len(pep["descriptions"]) == 2
        assert pep["total_records"] == 2

    def test_sorted_by_total_records_desc(self, client, db_session,
                                           sample_cycle, sample_collaborator):
        for day in range(1, 6):
            _add_record(db_session, sample_cycle, sample_collaborator,
                        pep="HIGH", desc="H", day=day)
        _add_record(db_session, sample_cycle, sample_collaborator,
                    pep="LOW", desc="L", day=10)
        result = client.get("/api/peps").json()
        codes = [p["code"] for p in result]
        assert codes.index("HIGH") < codes.index("LOW")

    def test_filter_by_cycle(self, client, db_session, sample_collaborator):
        c1 = Cycle(name="FC1", start_date=date(2026, 4, 1),
                   end_date=date(2026, 4, 30), is_quarantine=False)
        c2 = Cycle(name="FC2", start_date=date(2026, 5, 1),
                   end_date=date(2026, 5, 31), is_quarantine=False)
        db_session.add_all([c1, c2]); db_session.commit()
        _add_record(db_session, c1, sample_collaborator, pep="PEP-C1")
        _add_record(db_session, c2, sample_collaborator, pep="PEP-C2")

        result = client.get(f"/api/peps?cycle_id={c1.id}").json()
        codes = [p["code"] for p in result]
        assert "PEP-C1" in codes
        assert "PEP-C2" not in codes

    def test_filter_by_collaborator(self, client, db_session, sample_cycle):
        c1 = Collaborator(name="Filt1"); db_session.add(c1); db_session.commit()
        c2 = Collaborator(name="Filt2"); db_session.add(c2); db_session.commit()
        _add_record(db_session, sample_cycle, c1, pep="PEP-F1")
        _add_record(db_session, sample_cycle, c2, pep="PEP-F2")

        result = client.get(f"/api/peps?collaborator_id={c1.id}").json()
        codes = [p["code"] for p in result]
        assert "PEP-F1" in codes
        assert "PEP-F2" not in codes
