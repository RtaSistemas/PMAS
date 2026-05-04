from __future__ import annotations

import io
from datetime import date

import pandas as pd
import pytest

from backend.app.models import Collaborator, Cycle, TimesheetRecord
from backend.app.services.ingestion import _str_or_none, ingest_file


def _csv(*rows: dict) -> bytes:
    """Build a minimal CSV with the columns the ingestion service expects."""
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


BASE_ROW = {
    "Colaborador": "João Silva",
    "Data": "15/01/2026",
    "Horas totais (decimal)": 8.0,
    "Hora extra": "Não",
    "Hora sobreaviso": "Não",
    "Código PEP": "60OP-001",
    "PEP": "Projeto Alpha",
}


class TestIngestFile:
    def test_creates_collaborator(self, db_session, sample_cycle):
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        collab = db_session.query(Collaborator).filter_by(name="João Silva").first()
        assert collab is not None

    def test_creates_timesheet_record(self, db_session, sample_cycle):
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        assert summary["records_inserted"] == 1
        assert summary["records_skipped"] == 0

    def test_uses_existing_cycle(self, db_session, sample_cycle):
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        assert summary["quarantine_cycles_created"] == 0
        record = db_session.query(TimesheetRecord).first()
        assert record.cycle_id == sample_cycle.id

    def test_creates_quarantine_cycle_for_unknown_date(self, db_session):
        row = {**BASE_ROW, "Data": "10/09/2099"}
        summary = ingest_file(_csv(row), "t.csv", db_session)
        assert summary["quarantine_cycles_created"] == 1
        q = db_session.query(Cycle).filter_by(is_quarantine=True).first()
        assert q is not None
        assert "Quarentena" in q.name

    def test_deduplication(self, db_session, sample_cycle):
        csv = _csv(BASE_ROW, BASE_ROW)
        summary = ingest_file(csv, "t.csv", db_session)
        assert summary["records_inserted"] == 1
        assert summary["records_skipped"] == 1

    def test_same_day_normal_hours_different_start_time_all_inserted(self, db_session, sample_cycle):
        row1 = {**BASE_ROW, "Hora Inicial [H]": "08:00"}
        row2 = {**BASE_ROW, "Hora Inicial [H]": "10:00"}
        summary = ingest_file(_csv(row1, row2), "t.csv", db_session)
        assert summary["records_inserted"] == 2
        assert summary["records_skipped"] == 0

    def test_same_day_same_start_time_is_duplicate(self, db_session, sample_cycle):
        row1 = {**BASE_ROW, "Hora Inicial [H]": "08:00"}
        row2 = {**BASE_ROW, "Hora Inicial [H]": "08:00"}
        summary = ingest_file(_csv(row1, row2), "t.csv", db_session)
        assert summary["records_inserted"] == 1
        assert summary["records_skipped"] == 1

    def test_empty_start_time_treated_as_none_deduplicates(self, db_session, sample_cycle):
        row1 = {**BASE_ROW, "Hora Inicial [H]": ""}
        row2 = {**BASE_ROW, "Hora Inicial [H]": ""}
        summary = ingest_file(_csv(row1, row2), "t.csv", db_session)
        assert summary["records_inserted"] == 1
        assert summary["records_skipped"] == 1

    def test_different_hour_types_same_day_all_inserted(self, db_session, sample_cycle):
        normal_row  = {**BASE_ROW, "Hora extra": "Não", "Hora sobreaviso": "Não"}
        extra_row   = {**BASE_ROW, "Hora extra": "Sim", "Hora sobreaviso": "Não"}
        standby_row = {**BASE_ROW, "Hora extra": "Não", "Hora sobreaviso": "Sim"}
        summary = ingest_file(_csv(normal_row, extra_row, standby_row), "t.csv", db_session)
        assert summary["records_inserted"] == 3
        assert summary["records_skipped"] == 0
        records = db_session.query(TimesheetRecord).all()
        assert sum(r.normal_hours for r in records) == 8.0
        assert sum(r.extra_hours for r in records) == 8.0
        assert sum(r.standby_hours for r in records) == 8.0

    def test_deduplication_across_calls(self, db_session, sample_cycle):
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        summary2 = ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        # Second upload replaces previous data — idempotent, not additive
        assert summary2["records_inserted"] == 1
        assert summary2["records_skipped"] == 0
        assert db_session.query(TimesheetRecord).count() == 1

    def test_extra_hours(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Hora extra": "Sim", "Hora sobreaviso": "Não"}
        ingest_file(_csv(row), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).first()
        assert r.extra_hours == 8.0
        assert r.normal_hours == 0.0
        assert r.standby_hours == 0.0

    def test_standby_hours(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Hora extra": "Não", "Hora sobreaviso": "Sim"}
        ingest_file(_csv(row), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).first()
        assert r.standby_hours == 8.0
        assert r.normal_hours == 0.0

    def test_normal_hours_default(self, db_session, sample_cycle):
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).first()
        assert r.normal_hours == 8.0
        assert r.extra_hours == 0.0

    def test_pep_fields_populated(self, db_session, sample_cycle):
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).first()
        assert r.pep_wbs == "60OP-001"
        assert r.pep_description == "Projeto Alpha"

    def test_missing_required_column_raises(self, db_session):
        bad_csv = b"Colaborador,Data\nJoao,01/01/2026\n"
        with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
            ingest_file(bad_csv, "t.csv", db_session)

    def test_empty_pep_becomes_none(self, db_session, sample_cycle):
        row = {
            "Colaborador": "Ana",
            "Data": "15/01/2026",
            "Horas totais (decimal)": 4.0,
            "Código PEP": "",
            "PEP": "",
        }
        ingest_file(_csv(row), "t.csv", db_session)
        r = db_session.query(TimesheetRecord).first()
        assert r.pep_wbs is None
        assert r.pep_description is None

    def test_xlsx_accepted(self, db_session, sample_cycle):
        buf = io.BytesIO()
        df = pd.DataFrame([BASE_ROW])
        df.to_excel(buf, index=False)
        summary = ingest_file(buf.getvalue(), "dados.xlsx", db_session)
        assert summary["records_inserted"] == 1

    def test_closed_cycle_rejected_for_user(self, db_session, sample_cycle):
        from backend.app.services.ingestion import ClosedCycleError
        sample_cycle.is_closed = True
        db_session.commit()
        with pytest.raises(ClosedCycleError):
            ingest_file(_csv(BASE_ROW), "t.csv", db_session, user_role="user")

    def test_closed_cycle_allowed_for_admin(self, db_session, sample_cycle):
        sample_cycle.is_closed = True
        db_session.commit()
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session, user_role="admin")
        assert summary["records_inserted"] == 1

    def test_default_user_role_is_admin(self, db_session, sample_cycle):
        # calling without user_role keeps backward-compatible admin behaviour
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        assert summary["records_inserted"] == 1


class TestStrOrNone:
    def test_none_input(self):
        assert _str_or_none(None) is None

    def test_empty_string(self):
        assert _str_or_none("") is None

    def test_nan_string(self):
        assert _str_or_none("nan") is None

    def test_valid_string(self):
        assert _str_or_none("  60OP-001  ") == "60OP-001"

    def test_whitespace_only(self):
        assert _str_or_none("   ") is None


# ===========================================================================
# Tests for Issue #50 fix: ACL authorization + surgical (pep_wbs, cycle) delete
# ===========================================================================

class TestAuthorizationFilter:
    """Layer 1 — Silent filter for unauthorized PEPs."""

    def _make_user(self, db_session, username="pm1", role="user"):
        import bcrypt
        from backend.app.models import User
        u = User(
            username=username,
            hashed_password=bcrypt.hashpw(b"pass", bcrypt.gensalt()).decode(),
            role=role,
        )
        db_session.add(u)
        db_session.flush()
        return u

    def _make_project(self, db_session, pep_wbs, manager_id=None):
        from backend.app.models import Project
        p = Project(pep_wbs=pep_wbs, name=pep_wbs, manager_id=manager_id)
        db_session.add(p)
        db_session.flush()
        return p

    def test_admin_can_upload_any_pep(self, db_session, sample_cycle):
        """Admin bypasses all PEP restrictions."""
        user = self._make_user(db_session, "admin_user", role="admin")
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session,
                              user_role="admin", user_id=user.id)
        assert summary["records_inserted"] == 1
        assert not any("permissão" in w for w in summary["warnings"])

    def test_user_without_access_rows_discarded_silently(self, db_session, sample_cycle):
        """Non-admin with no project access has rows silently discarded + warning."""
        user = self._make_user(db_session, "no_access_user")
        self._make_project(db_session, "60OP-001")  # project exists, user NOT manager
        db_session.commit()
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session,
                              user_role="user", user_id=user.id)
        assert summary["records_inserted"] == 0
        assert any("permissão" in w for w in summary["warnings"])

    def test_manager_id_grants_auto_access(self, db_session, sample_cycle):
        """User registered as project manager gets automatic upload access."""
        user = self._make_user(db_session, "pm_auto")
        self._make_project(db_session, "60OP-001", manager_id=user.id)
        db_session.commit()
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session,
                              user_role="user", user_id=user.id)
        assert summary["records_inserted"] == 1
        assert not any("permissão" in w for w in summary["warnings"])

    def test_acl_grant_gives_access(self, db_session, sample_cycle):
        """Explicit UserProjectAccess entry grants access regardless of manager_id."""
        from backend.app.models import UserProjectAccess
        user = self._make_user(db_session, "pm_acl")
        project = self._make_project(db_session, "60OP-001")
        db_session.add(UserProjectAccess(user_id=user.id, project_id=project.id))
        db_session.commit()
        summary = ingest_file(_csv(BASE_ROW), "t.csv", db_session,
                              user_role="user", user_id=user.id)
        assert summary["records_inserted"] == 1

    def test_partial_access_filters_unauthorized_keeps_authorized(self, db_session, sample_cycle):
        """If file has PEP-A (authorized) and PEP-B (unauthorized), only PEP-A is inserted."""
        user = self._make_user(db_session, "pm_partial")
        self._make_project(db_session, "60OP-001", manager_id=user.id)
        self._make_project(db_session, "60OP-002")  # user NOT manager
        db_session.commit()
        row_b = {**BASE_ROW, "Código PEP": "60OP-002", "PEP": "Projeto Beta"}
        summary = ingest_file(_csv(BASE_ROW, row_b), "t.csv", db_session,
                              user_role="user", user_id=user.id)
        assert summary["records_inserted"] == 1  # only PEP-A row
        assert any("permissão" in w for w in summary["warnings"])


class TestSurgicalDeletion:
    """Layer 3 — (pep_wbs, cycle) deletion scope."""

    def test_reupload_same_pep_replaces_all_collabs(self, db_session, sample_cycle):
        """Re-uploading PEP-A with fewer collabs must remove absent collab records."""
        row_b = {**BASE_ROW, "Colaborador": "Maria Souza"}
        # First upload: João + Maria on PEP 60OP-001
        ingest_file(_csv(BASE_ROW, row_b), "t.csv", db_session)
        count_before = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.pep_wbs == "60OP-001"
        ).count()
        assert count_before == 2

        # Second upload: only João on PEP 60OP-001 (Maria removed from file)
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        count_after = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.pep_wbs == "60OP-001"
        ).count()
        # Maria's record must be gone — no orphan data
        assert count_after == 1

    def test_uploading_pep_a_does_not_touch_pep_b(self, db_session, sample_cycle):
        """PM uploading PEP-A must not delete PEP-B rows in the same cycle."""
        row_b = {**BASE_ROW, "Código PEP": "60OP-002", "PEP": "Projeto Beta",
                 "Colaborador": "Maria Souza"}
        # Seed both PEPs
        ingest_file(_csv(BASE_ROW, row_b), "t.csv", db_session)

        # Re-upload only PEP-A
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)

        # PEP-B record must still be there
        pep_b_count = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.pep_wbs == "60OP-002"
        ).count()
        assert pep_b_count == 1

    def test_null_pep_deletion_scoped_to_collaborator(self, db_session, sample_cycle):
        """NULL-pep rows are deleted by (collaborator, cycle) — not by PEP scope."""
        row_no_pep = {
            "Colaborador": "Anon User",
            "Data": "15/01/2026",
            "Horas totais (decimal)": 6.0,
            "Hora extra": "Não",
            "Hora sobreaviso": "Não",
        }
        row_other_no_pep = {**row_no_pep, "Colaborador": "Other Anon"}
        # Seed two null-pep collabs
        ingest_file(_csv(row_no_pep, row_other_no_pep), "t.csv", db_session)
        assert db_session.query(TimesheetRecord).filter(
            TimesheetRecord.pep_wbs.is_(None)
        ).count() == 2

        # Re-upload only first collab (no PEP code)
        ingest_file(_csv(row_no_pep), "t.csv", db_session)

        # Only 'Anon User' is replaced; 'Other Anon' must remain
        assert db_session.query(TimesheetRecord).filter(
            TimesheetRecord.pep_wbs.is_(None)
        ).count() == 2  # Anon User (new) + Other Anon (untouched)
