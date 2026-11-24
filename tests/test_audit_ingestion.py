"""Regression tests for the ingestion audit findings (A2-A14)."""
from __future__ import annotations

import io
import unicodedata
from datetime import date

import pandas as pd
import pytest

from backend.app.models import (
    Collaborator,
    CollaboratorCycleSummary,
    Cycle,
    PepCycleSummary,
    Project,
    ProjectAlert,
    QuarantineRecord,
    TimesheetRecord,
    UploadSession,
    User,
    UserProjectAccess,
)
from backend.app.services.ingestion import _safe_hours, ingest_file


def _csv(*rows: dict) -> bytes:
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def _row(name="Ana", day="12/01/2026", hours=8.0, pep="AA-0001", **extra) -> dict:
    r = {
        "Colaborador": name,
        "Data": day,
        "Horas totais (decimal)": hours,
        "Hora extra": "Não",
        "Hora sobreaviso": "Não",
        "Código PEP": pep,
        "PEP": "Projeto A",
    }
    r.update(extra)
    return r


# ---------------------------------------------------------------------------
# A2 — collaborator summary after surgical delete
# ---------------------------------------------------------------------------

class TestA2SummaryAfterReplace:
    def test_removed_collaborator_summary_is_cleared(self, db_session, sample_cycle):
        ingest_file(_csv(_row("Ana", hours=8), _row("Bob", hours=8)), "a.csv", db_session)
        ingest_file(_csv(_row("Ana", hours=4)), "b.csv", db_session)

        bob = db_session.query(Collaborator).filter_by(name="Bob").one()
        assert db_session.query(TimesheetRecord).filter_by(collaborator_id=bob.id).count() == 0
        assert (
            db_session.query(CollaboratorCycleSummary)
            .filter_by(collaborator_id=bob.id).count()
        ) == 0
        ana = db_session.query(Collaborator).filter_by(name="Ana").one()
        s = db_session.query(CollaboratorCycleSummary).filter_by(collaborator_id=ana.id).one()
        assert s.total_hours == 4.0

    def test_effort_endpoint_does_not_list_removed_collaborator(self, client, db_session, sample_cycle):
        ingest_file(_csv(_row("Ana", hours=8), _row("Bob", hours=8)), "a.csv", db_session)
        ingest_file(_csv(_row("Ana", hours=4)), "b.csv", db_session)
        data = client.get("/api/v2/effort").json()
        assert "Bob" not in str(data)

    def test_pep_and_collab_summary_cleared_when_file_leaves_scope_empty(self, db_session, sample_cycle):
        ingest_file(_csv(_row("Ana", hours=8), _row("Bob", hours=8)), "a.csv", db_session)
        # Zero-hour row: valid, wipes the (PEP, cycle) scope, inserts nothing.
        ingest_file(_csv(_row("Ana", hours=0)), "b.csv", db_session)
        assert db_session.query(TimesheetRecord).count() == 0
        assert db_session.query(PepCycleSummary).count() == 0
        assert db_session.query(CollaboratorCycleSummary).count() == 0


# ---------------------------------------------------------------------------
# A3 — replacement info message
# ---------------------------------------------------------------------------

class TestA3ReplacementInfo:
    def test_info_reports_replaced_rows(self, db_session, sample_cycle):
        rows = [_row("Ana", day=f"{d:02d}/01/2026") for d in range(5, 10)]
        ingest_file(_csv(*rows), "a.csv", db_session)
        res = ingest_file(_csv(_row("Ana", day="12/01/2026")), "b.csv", db_session)
        msg = [i for i in res["infos"] if "substituído" in i]
        assert len(msg) == 1
        assert "AA-0001" in msg[0] and "Jan/2026" in msg[0]
        assert "5 registro(s) anterior(es) substituído(s) por 1" in msg[0]
        sess = db_session.get(UploadSession, res["upload_session_id"])
        assert any("substituído" in i for i in sess.infos_detail)

    def test_no_info_on_first_upload(self, db_session, sample_cycle):
        res = ingest_file(_csv(_row("Ana")), "a.csv", db_session)
        assert not [i for i in res["infos"] if "substituído" in i]


# ---------------------------------------------------------------------------
# A4a / A14 — ACL with blank PEP
# ---------------------------------------------------------------------------

def _restricted_user(db, pep="AA-0001"):
    user = User(username="joana", hashed_password="x", role="user")
    proj = Project(pep_wbs=pep, name="P", status="ativo")
    db.add_all([user, proj])
    db.commit()
    db.add(UserProjectAccess(user_id=user.id, project_id=proj.id))
    db.commit()
    return user


class TestA4aBlankPepAcl:
    def test_blank_pep_rows_discarded_for_restricted_user(self, db_session, sample_cycle):
        user = _restricted_user(db_session)
        res = ingest_file(
            _csv(_row("Ana", pep="AA-0001"), _row("Bob", pep="")),
            "a.csv", db_session, user_role="user", user_id=user.id, username="joana",
        )
        assert res["records_inserted"] == 1
        assert db_session.query(TimesheetRecord).filter(TimesheetRecord.pep_wbs.is_(None)).count() == 0
        assert any("sem PEP" in w and "1" in w for w in res["warnings"])

    def test_all_blank_pep_is_refused(self, db_session, sample_cycle):
        from fastapi import HTTPException
        user = _restricted_user(db_session)
        with pytest.raises(HTTPException) as exc:
            ingest_file(
                _csv(_row("Bob", pep="")), "a.csv", db_session,
                user_role="user", user_id=user.id, username="joana",
            )
        assert exc.value.status_code == 403

    def test_admin_keeps_blank_pep(self, db_session, sample_cycle):
        res = ingest_file(_csv(_row("Bob", pep="")), "a.csv", db_session)
        assert res["records_inserted"] == 1


class TestA14AclCounts:
    def test_discarded_rows_counted_in_skipped(self, db_session, sample_cycle):
        user = _restricted_user(db_session)
        res = ingest_file(
            _csv(_row("Ana", pep="AA-0001"), _row("Bob", pep="ZZ-9999"), _row("Cid", pep="")),
            "a.csv", db_session, user_role="user", user_id=user.id, username="joana",
        )
        assert res["records_inserted"] == 1
        assert res["records_skipped"] == 2
        assert (
            res["records_inserted"] + res["records_skipped"] + res["quarantine_records_added"] == 3
        )
        sess = db_session.get(UploadSession, res["upload_session_id"])
        assert sess.records_skipped == 2


# ---------------------------------------------------------------------------
# A5 — quarantine approve guards
# ---------------------------------------------------------------------------

def _quarantine(db, raw: dict) -> int:
    rec = QuarantineRecord(raw_data=raw, quarantine_reason="teste")
    db.add(rec)
    db.commit()
    return rec.id


def _raw(**kw) -> dict:
    base = {
        "Colaborador": "Ana", "Data": "12/01/2026", "Horas totais (decimal)": 8.0,
        "Hora extra": "Não", "Hora sobreaviso": "Não",
        "Código PEP": "AA-0001", "PEP": "Projeto A",
    }
    base.update(kw)
    return base


class TestA5QuarantineApprove:
    def test_locked_project_refused(self, client, db_session, sample_cycle):
        db_session.add(Project(pep_wbs="AA-0001", name="Enc", status="encerrado"))
        db_session.commit()
        qid = _quarantine(db_session, _raw())
        r = client.post(f"/api/quarantine/{qid}/approve")
        assert r.status_code == 422
        assert "encerrado" in r.json()["detail"].lower() or "suspenso" in r.json()["detail"].lower()
        assert db_session.query(TimesheetRecord).count() == 0

    def test_negative_hours_refused(self, client, db_session, sample_cycle):
        qid = _quarantine(db_session, _raw(**{"Horas totais (decimal)": -3.0}))
        r = client.post(f"/api/quarantine/{qid}/approve")
        assert r.status_code == 422
        assert db_session.query(TimesheetRecord).count() == 0

    def test_exact_duplicate_returns_409(self, client, db_session, sample_cycle):
        ingest_file(_csv(_row("Ana", hours=8)), "a.csv", db_session)
        qid = _quarantine(db_session, _raw())
        r = client.post(f"/api/quarantine/{qid}/approve")
        assert r.status_code == 409
        assert db_session.query(TimesheetRecord).count() == 1
        db_session.expire_all()
        assert db_session.get(QuarantineRecord, qid).review_status != "approved"

    def test_valid_approve_still_works_and_updates_summary(self, client, db_session, sample_cycle):
        qid = _quarantine(db_session, _raw())
        r = client.post(f"/api/quarantine/{qid}/approve")
        assert r.status_code == 200
        assert db_session.query(TimesheetRecord).count() == 1
        assert db_session.query(PepCycleSummary).one().total_hours == 8.0
        assert client.post(f"/api/quarantine/{qid}/approve").status_code == 409


# ---------------------------------------------------------------------------
# A6 — collaborator name normalization
# ---------------------------------------------------------------------------

class TestA6Names:
    def test_nfc_nfd_same_collaborator(self, db_session, sample_cycle):
        nfc = unicodedata.normalize("NFC", "José")
        nfd = unicodedata.normalize("NFD", "José")
        assert nfc != nfd
        ingest_file(_csv(_row(nfc, day="12/01/2026"), _row(nfd, day="13/01/2026")), "a.csv", db_session)
        names = [c.name for c in db_session.query(Collaborator).all()]
        assert names == [nfc]

    def test_whitespace_collapsed(self, db_session, sample_cycle):
        ingest_file(
            _csv(_row("José  Silva", day="12/01/2026"), _row("  José Silva ", day="13/01/2026")),
            "a.csv", db_session,
        )
        names = [c.name for c in db_session.query(Collaborator).all()]
        assert names == ["José Silva"]

    def test_case_not_merged_but_similarity_info(self, db_session, sample_cycle):
        ingest_file(_csv(_row("José")), "a.csv", db_session)
        res = ingest_file(_csv(_row("jose", day="13/01/2026")), "b.csv", db_session)
        assert db_session.query(Collaborator).count() == 2
        assert any("José" in i and "jose" in i and "semelhante" in i for i in res["infos"])

    def test_no_similarity_info_for_unrelated(self, db_session, sample_cycle):
        ingest_file(_csv(_row("José")), "a.csv", db_session)
        res = ingest_file(_csv(_row("Maria", day="13/01/2026")), "b.csv", db_session)
        assert not any("semelhante" in i for i in res["infos"])


# ---------------------------------------------------------------------------
# A7 — file loading
# ---------------------------------------------------------------------------

HDR = "Colaborador;Data;Horas totais (decimal);Código PEP;PEP\n"


class TestA7Loading:
    def test_semicolon_with_decimal_comma(self, db_session, sample_cycle):
        data = (HDR + "Ana;12/01/2026;8,5;AA-0001;Proj\n").encode("utf-8")
        res = ingest_file(data, "a.csv", db_session)
        assert res["records_inserted"] == 1
        assert db_session.query(TimesheetRecord).one().normal_hours == 8.5

    def test_cp1252_encoding(self, db_session, sample_cycle):
        data = (HDR + "José;12/01/2026;8;AA-0001;Proj\n").encode("cp1252")
        res = ingest_file(data, "a.csv", db_session)
        assert res["records_inserted"] == 1
        assert db_session.query(Collaborator).one().name == "José"

    def test_utf8_bom(self, db_session, sample_cycle):
        data = ("﻿" + HDR + "Ana;12/01/2026;8;AA-0001;Proj\n").encode("utf-8")
        assert ingest_file(data, "a.csv", db_session)["records_inserted"] == 1

    def test_case_insensitive_columns(self, db_session, sample_cycle):
        data = (
            " colaborador ;DATA;horas totais (decimal);CÓDIGO pep;pep\n"
            "Ana;12/01/2026;8;AA-0001;Proj\n"
        ).encode("utf-8")
        res = ingest_file(data, "a.csv", db_session)
        assert res["records_inserted"] == 1
        assert db_session.query(TimesheetRecord).one().pep_wbs == "AA-0001"

    def test_empty_file(self, db_session):
        with pytest.raises(ValueError, match="vazio"):
            ingest_file(b"", "a.csv", db_session)

    def test_header_only(self, db_session):
        with pytest.raises(ValueError, match="cabeçalho"):
            ingest_file(HDR.encode("utf-8"), "a.csv", db_session)

    def test_corrupt_excel(self, db_session):
        with pytest.raises(ValueError) as exc:
            ingest_file(b"not an excel file", "a.xlsx", db_session)
        assert "Excel" in str(exc.value)

    def test_missing_columns_still_reported(self, db_session):
        with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
            ingest_file(b"A,B\n1,2\n", "a.csv", db_session)


# ---------------------------------------------------------------------------
# A8 — alert auto-resolution when data disappears
# ---------------------------------------------------------------------------

class TestA8AlertResolve:
    def test_budget_alert_resolved_when_consumption_zero(self, db_session, sample_cycle):
        from backend.app.services.notifications_svc import notify_threshold_crossings

        db_session.add(Project(pep_wbs="AA-0001", name="P", budget_hours=10.0, status="ativo"))
        db_session.commit()
        ingest_file(_csv(_row("Ana", hours=12)), "a.csv", db_session)
        notify_threshold_crossings(db_session, ["AA-0001"])
        db_session.commit()
        assert db_session.query(ProjectAlert).filter_by(is_resolved=False).count() == 1

        ingest_file(_csv(_row("Ana", hours=0)), "b.csv", db_session)
        assert db_session.query(PepCycleSummary).count() == 0
        notify_threshold_crossings(db_session, ["AA-0001"])
        db_session.commit()
        assert db_session.query(ProjectAlert).filter_by(is_resolved=False).count() == 0

    def test_schedule_risk_resolved_when_data_disappears(self, db_session, sample_cycle):
        from backend.app.services.notifications_svc import (
            _upsert_project_alert,
            notify_schedule_risk,
        )

        p = Project(pep_wbs="AA-0001", name="P", budget_hours=100.0, status="ativo")
        db_session.add(p)
        db_session.commit()
        _upsert_project_alert(db_session, p.id, "AA-0001", "schedule_risk", "warning", "x")
        db_session.commit()
        notify_schedule_risk(db_session, ["AA-0001"])
        db_session.commit()
        assert db_session.query(ProjectAlert).filter_by(is_resolved=False).count() == 0


# ---------------------------------------------------------------------------
# A9 — hours parsing
# ---------------------------------------------------------------------------

class TestA9Hours:
    @pytest.mark.parametrize("v", ["1e1", "1E1", "1e-2", "1_0", "0x10", "infinity"])
    def test_rejects_non_plain_numbers(self, v):
        assert _safe_hours(v) is None

    @pytest.mark.parametrize("v,exp", [("8,5", 8.5), ("8.5", 8.5), ("8", 8.0), (" 7 ", 7.0), ("-3", -3.0), (8, 8.0), (0.5, 0.5)])
    def test_keeps_plain_numbers(self, v, exp):
        assert _safe_hours(v) == exp

    def test_empty_cell_reason_has_no_nan(self, db_session, sample_cycle):
        data = (HDR + "Ana;12/01/2026;;AA-0001;Proj\n").encode("utf-8")
        res = ingest_file(data, "a.csv", db_session)
        assert res["quarantine_records_added"] == 1
        reason = db_session.query(QuarantineRecord).one().quarantine_reason
        assert "nan" not in reason.lower()
        assert "vazia" in reason


# ---------------------------------------------------------------------------
# A11 — PEP codes stay strings
# ---------------------------------------------------------------------------

class TestA11PepStrings:
    def test_csv_leading_zero_and_numeric(self, db_session, sample_cycle):
        data = (HDR + "Ana;12/01/2026;8;0123;Proj\nBob;12/01/2026;8;1001;Proj\n").encode("utf-8")
        ingest_file(data, "a.csv", db_session)
        peps = sorted(r.pep_wbs for r in db_session.query(TimesheetRecord).all())
        assert peps == ["0123", "1001"]

    def test_excel_numeric_pep_no_float_artifact(self, db_session, sample_cycle):
        df = pd.DataFrame([{
            "Colaborador": "Ana", "Data": "12/01/2026", "Horas totais (decimal)": 8,
            "Código PEP": 1001, "PEP": "Proj",
        }, {
            "Colaborador": "Bob", "Data": "12/01/2026", "Horas totais (decimal)": 8,
            "Código PEP": "0123", "PEP": "Proj",
        }])
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        ingest_file(buf.getvalue(), "a.xlsx", db_session)
        peps = sorted(r.pep_wbs for r in db_session.query(TimesheetRecord).all())
        assert peps == ["0123", "1001"]
