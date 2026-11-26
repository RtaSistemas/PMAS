"""Product decisions: same-day rows are summed, empty whitelist imports all, baselines are admin only."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from fastapi import HTTPException

from backend.app.models import (
    AuditLog, Collaborator, PepCycleSummary, Project, ProjectBaseline,
    QuarantineRecord, RateCard, SeniorityLevel, TimesheetRecord, User, UserProjectAccess,
)
from backend.app.routers.auth import hash_password
from backend.app.services.ingestion import ingest_file
from tests.test_audit_analytics import _as

ROW = {
    "Colaborador": "Ana", "Data": "10/01/2026", "Horas totais (decimal)": 3.0,
    "Hora extra": "Não", "Hora sobreaviso": "Não",
    "Código PEP": "AA-0001", "PEP": "Alpha",
}


def _csv(*rows) -> bytes:
    return pd.DataFrame(list(rows)).to_csv(index=False).encode("utf-8")


def _hrs(h, **kw):
    return {**ROW, "Horas totais (decimal)": h, **kw}


def _user(db, name="u1", role="user"):
    u = User(username=name, hashed_password=hash_password("pass123"), role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Decision 1: same-day rows with different hours are summed
# ---------------------------------------------------------------------------

class TestSameDaySum:
    def test_different_hours_are_summed(self, db_session, sample_cycle):
        out = ingest_file(_csv(_hrs(3.0), _hrs(5.0)), "t.csv", db_session)
        recs = db_session.query(TimesheetRecord).all()
        assert len(recs) == 1 and recs[0].normal_hours == 8.0
        assert out["records_skipped"] == 0
        assert out["records_summed"] == 1

    def test_exact_duplicate_after_sum_is_discarded(self, db_session, sample_cycle):
        out = ingest_file(_csv(_hrs(3.0), _hrs(5.0), _hrs(5.0)), "t.csv", db_session)
        recs = db_session.query(TimesheetRecord).all()
        assert len(recs) == 1 and recs[0].normal_hours == 8.0
        assert out["records_skipped"] == 1
        assert any("duplicata ignorada" in i for i in out["infos"])

    def test_totals_invariant_with_sum_dup_quarantine(self, db_session, sample_cycle):
        bad = _hrs(2.0, Data="10/09/2020")  # no cycle -> quarantine
        out = ingest_file(_csv(_hrs(3.0), _hrs(5.0), _hrs(5.0), bad), "t.csv", db_session)
        total = out["records_inserted"] + out["records_skipped"] + out["quarantine_records_added"]
        assert total == 4
        # inserted counts file rows whose hours are stored; summed rows are among them
        assert out["records_inserted"] == 2 and out["records_summed"] == 1
        assert db_session.query(TimesheetRecord).count() == out["records_inserted"] - out["records_summed"]

    def test_cost_uses_frozen_rate_on_summed_hours(self, db_session, sample_cycle):
        lvl = SeniorityLevel(name="Pleno")
        db_session.add(lvl)
        db_session.commit()
        db_session.add(RateCard(seniority_level_id=lvl.id, hourly_rate=100.0, valid_from=date(2025, 1, 1)))
        db_session.add(Collaborator(name="Ana", seniority_level_id=lvl.id))
        db_session.commit()
        ingest_file(_csv(_hrs(3.0), _hrs(5.0)), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).one()
        assert r.cost_per_hour == 100.0 and r.normal_cost == pytest.approx(800.0)

    def test_extra_hours_are_summed_with_multiplier(self, db_session, sample_cycle):
        lvl = SeniorityLevel(name="Sr")
        db_session.add(lvl)
        db_session.commit()
        db_session.add(RateCard(seniority_level_id=lvl.id, hourly_rate=100.0, valid_from=date(2025, 1, 1)))
        db_session.add(Collaborator(name="Ana", seniority_level_id=lvl.id))
        db_session.commit()
        ingest_file(_csv(_hrs(1.0, **{"Hora extra": "Sim"}), _hrs(2.0, **{"Hora extra": "Sim"})),
                    "t.csv", db_session)
        r = db_session.query(TimesheetRecord).one()
        assert r.extra_hours == 3.0 and r.extra_cost == pytest.approx(3.0 * 100.0 * 1.5)

    def test_different_peps_are_not_summed(self, db_session, sample_cycle):
        out = ingest_file(_csv(_hrs(3.0), _hrs(5.0, **{"Código PEP": "BB-0002"})), "t.csv", db_session)
        assert db_session.query(TimesheetRecord).count() == 2
        assert out["records_summed"] == 0

    def test_info_text_for_summed_rows(self, db_session, sample_cycle):
        out = ingest_file(_csv(_hrs(3.0), _hrs(5.0)), "t.csv", db_session)
        assert ("1 linha(s) do mesmo dia somada(s): Ana em 10/01/2026 | PEP AA-0001 "
                "(3,00 h + 5,00 h = 8,00 h)") in out["infos"]

    def test_info_lists_are_capped(self, db_session, sample_cycle):
        rows = []
        for d in range(1, 26):  # 25 days, each with 2 different rows, plus 25 exact duplicates
            day = f"{d:02d}/01/2026"
            rows += [_hrs(1.0, Data=day), _hrs(2.0, Data=day), _hrs(2.0, Data=day)]
        out = ingest_file(_csv(*rows), "t.csv", db_session)
        assert out["records_summed"] == 25 and out["records_skipped"] == 25
        summed = [i for i in out["infos"] if "do mesmo dia somada" in i]
        assert len(summed) == 1 and "+15 outras" in summed[0]
        dups = [i for i in out["infos"] if "duplicata" in i]
        assert len(dups) == 11 and dups[-1].startswith("+15 outras duplicatas")

    def test_daily_rule_counts_the_summed_hours(self, db_session, sample_cycle):
        out = ingest_file(_csv(_hrs(10.0), _hrs(10.5), _hrs(9.0)), "t.csv", db_session)
        assert db_session.query(TimesheetRecord).one().normal_hours == 29.5
        assert any("Ana" in w and "24" in w for w in out["warnings"])

    def test_daily_rule_ignores_discarded_exact_duplicates(self, db_session, sample_cycle):
        # three identical 10 h rows: two are exact duplicates; 10 h is stored, so no >24 h warning
        out = ingest_file(_csv(_hrs(10.0), _hrs(10.0), _hrs(10.0)), "t.csv", db_session)
        assert db_session.query(TimesheetRecord).one().normal_hours == 10.0
        assert not any("24" in w and "Ana" in w for w in out["warnings"])

    def test_summaries_match_raw(self, db_session, sample_cycle):
        ingest_file(_csv(_hrs(3.0), _hrs(5.0)), "t.csv", db_session)
        s = db_session.query(PepCycleSummary).one()
        assert s.normal_hours == 8.0

    def test_reupload_is_idempotent(self, db_session, sample_cycle):
        data = _csv(_hrs(3.0), _hrs(5.0))
        ingest_file(data, "t.csv", db_session)
        ingest_file(data, "t.csv", db_session)
        assert db_session.query(TimesheetRecord).one().normal_hours == 8.0


class TestApproveQuarantineSums:
    def _quarantine(self, db, hours):
        qr = QuarantineRecord(
            raw_data={"Colaborador": "Ana", "Data": "10/01/2026", "Horas totais (decimal)": hours,
                      "Código PEP": "AA-0001", "PEP": "Alpha"},
            quarantine_reason="test",
        )
        db.add(qr)
        db.commit()
        return qr.id

    def test_approve_sums_into_existing_record(self, client, db_session, sample_cycle):
        ingest_file(_csv(_hrs(3.0)), "t.csv", db_session)
        qid = self._quarantine(db_session, 5.0)
        assert client.post(f"/api/quarantine/{qid}/approve").status_code == 200
        db_session.expire_all()
        assert db_session.query(TimesheetRecord).one().normal_hours == 8.0
        assert db_session.query(PepCycleSummary).one().normal_hours == 8.0

    def test_approve_exact_duplicate_still_409(self, client, db_session, sample_cycle):
        ingest_file(_csv(_hrs(3.0)), "t.csv", db_session)
        qid = self._quarantine(db_session, 3.0)
        assert client.post(f"/api/quarantine/{qid}/approve").status_code == 409
        assert db_session.query(TimesheetRecord).one().normal_hours == 3.0


# ---------------------------------------------------------------------------
# Decision 2: empty whitelist = access to all, also on upload
# ---------------------------------------------------------------------------

class TestEmptyWhitelistUpload:
    def test_user_without_whitelist_can_import_any_pep(self, db_session, sample_cycle):
        u = _user(db_session)
        out = ingest_file(_csv(ROW), "t.csv", db_session, user_role="user", user_id=u.id)
        assert out["records_inserted"] == 1

    def test_user_without_whitelist_can_import_row_without_pep(self, db_session, sample_cycle):
        u = _user(db_session)
        out = ingest_file(_csv({**ROW, "Código PEP": None, "PEP": None}), "t.csv", db_session,
                          user_role="user", user_id=u.id)
        assert out["records_inserted"] == 1

    def test_user_with_whitelist_keeps_restriction(self, db_session, sample_cycle):
        u = _user(db_session)
        p = Project(pep_wbs="OK-1", name="ok")
        db_session.add(p)
        db_session.commit()
        db_session.add(UserProjectAccess(user_id=u.id, project_id=p.id))
        db_session.commit()
        with pytest.raises(HTTPException) as e:
            ingest_file(_csv(ROW), "t.csv", db_session, user_role="user", user_id=u.id)
        assert e.value.status_code == 403
        out = ingest_file(_csv({**ROW, "Código PEP": "OK-1"}, ROW), "t.csv", db_session,
                          user_role="user", user_id=u.id)
        assert out["records_inserted"] == 1 and out["records_skipped"] == 1

    def test_upload_api_with_api_key_of_user_without_whitelist(self, client, db_session, sample_cycle):
        from backend.app.deps import get_current_user, get_current_user_allow_change, get_upload_user
        from backend.app.main import app
        saved = dict(app.dependency_overrides)
        admin = _user(db_session, "adm", role="admin")
        svc = _user(db_session, "svc")
        app.dependency_overrides[get_current_user] = lambda: admin
        app.dependency_overrides[get_current_user_allow_change] = lambda: admin
        app.dependency_overrides.pop(get_upload_user, None)
        try:
            created = client.post("/api/api-keys", json={"name": "Importer", "user_id": svc.id})
            assert created.status_code == 201, created.text
            raw = created.json()["key"]
            r = client.post("/api/upload-timesheet", headers={"X-API-Key": raw},
                            files={"file": ("ts.csv", _csv(ROW), "text/csv")})
            assert r.status_code == 200, r.text
            assert db_session.query(TimesheetRecord).count() == 1
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Decision 3: baselines are admin only and audited
# ---------------------------------------------------------------------------

@pytest.fixture
def proj(db_session):
    p = Project(pep_wbs="BL-1", name="BL", budget_hours=100, budget_cost=1000)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


class TestBaselines:
    def test_regular_user_cannot_write(self, client, db_session, proj):
        u = _user(db_session)
        bl = ProjectBaseline(project_id=proj.id, budget_hours=1, budget_cost=1, is_active=False)
        db_session.add(bl)
        db_session.commit()
        with _as(u) as c:
            assert c.post(f"/api/projects/{proj.id}/baseline", json={"label": "x"}).status_code == 403
            assert c.post(f"/api/projects/{proj.id}/baselines/{bl.id}/activate").status_code == 403
            assert c.delete(f"/api/projects/{proj.id}/baselines/{bl.id}").status_code == 403
        assert db_session.query(ProjectBaseline).count() == 1

    def test_user_with_access_can_read_list(self, client, db_session, proj):
        u = _user(db_session)
        with _as(u) as c:
            assert c.get(f"/api/projects/{proj.id}/baselines").status_code == 200

    def test_restricted_user_cannot_read_other_project(self, client, db_session, proj):
        u = _user(db_session)
        other = Project(pep_wbs="OTH", name="o")
        db_session.add(other)
        db_session.commit()
        db_session.add(UserProjectAccess(user_id=u.id, project_id=other.id))
        db_session.commit()
        with _as(u) as c:
            assert c.get(f"/api/projects/{proj.id}/baselines").status_code == 403

    def test_create_activate_delete_write_audit(self, client, db_session, proj):
        b1 = client.post(f"/api/projects/{proj.id}/baseline", json={"label": "v1"}).json()
        b2 = client.post(f"/api/projects/{proj.id}/baseline", json={"label": "v2"}).json()
        assert client.post(f"/api/projects/{proj.id}/baselines/{b1['id']}/activate").status_code == 200
        assert client.delete(f"/api/projects/{proj.id}/baselines/{b2['id']}").status_code == 200
        rows = db_session.query(AuditLog).filter_by(entity="baseline").order_by(AuditLog.id).all()
        assert [r.action for r in rows] == ["create", "create", "activate", "delete"]
        text = " ".join(str(r.__dict__) for r in rows)
        assert "BL-1" in text and "v1" in text and "v2" in text

    def test_delete_active_baseline_returns_409(self, client, db_session, proj):
        b1 = client.post(f"/api/projects/{proj.id}/baseline", json={"label": "v1"}).json()
        r = client.delete(f"/api/projects/{proj.id}/baselines/{b1['id']}")
        assert r.status_code == 409
        assert db_session.query(ProjectBaseline).count() == 1
        b2 = client.post(f"/api/projects/{proj.id}/baseline", json={"label": "v2"}).json()  # b2 active
        assert client.delete(f"/api/projects/{proj.id}/baselines/{b1['id']}").status_code == 200
        assert client.delete(f"/api/projects/{proj.id}/baselines/{b2['id']}").status_code == 409
