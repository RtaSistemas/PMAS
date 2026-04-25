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

    def test_deduplication_across_calls(self, db_session, sample_cycle):
        ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        summary2 = ingest_file(_csv(BASE_ROW), "t.csv", db_session)
        assert summary2["records_inserted"] == 0
        assert summary2["records_skipped"] == 1

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
