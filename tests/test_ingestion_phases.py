"""Unit tests for the extracted phase functions in services/ingestion.py.

Each test class covers one phase function independently.
"""
from __future__ import annotations

import io
from datetime import date, timedelta

import pandas as pd
import pytest

from backend.app.models import (
    Collaborator,
    Cycle,
    Project,
    TimesheetRecord,
    UserProjectAccess,
    ValidationRule,
)
from backend.app.services.ingestion import (
    _phase_aggregate_rules,
    _phase_authorize_peps,
    _phase_load_and_validate,
    _phase_prescan_dates,
    _phase_upsert_records,
    _phase_validate_rows,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

_JAN_2026_CYCLE_KWARGS = dict(
    name="Jan/2026",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 31),
)


def _make_cycle(db_session, **kwargs) -> Cycle:
    kw = {**_JAN_2026_CYCLE_KWARGS, **kwargs}
    cycle = Cycle(**kw)
    db_session.add(cycle)
    db_session.commit()
    db_session.refresh(cycle)
    return cycle


def _make_collaborator(db_session, name: str = "João Silva") -> Collaborator:
    c = Collaborator(name=name)
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def _rules(db_session) -> list:
    return (
        db_session.query(ValidationRule)
        .filter(ValidationRule.is_active == True)  # noqa: E712
        .order_by(ValidationRule.order)
        .all()
    )


def _df_from_rows(*rows: dict) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(_csv(*rows)))
    df.columns = [c.strip() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# Phase 0: _phase_load_and_validate
# ---------------------------------------------------------------------------

class TestPhaseLoadAndValidate:
    def test_valid_csv_returns_dataframe(self):
        data = _csv(BASE_ROW)
        df = _phase_load_and_validate(data, "test.csv")
        assert len(df) == 1
        assert "Colaborador" in df.columns
        assert "Data" in df.columns
        assert "Horas totais (decimal)" in df.columns

    def test_missing_required_column_raises_value_error(self):
        bad_csv = b"Colaborador,Data\nJoao,01/01/2026\n"
        with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
            _phase_load_and_validate(bad_csv, "test.csv")

    def test_empty_file_raises_value_error(self):
        headers_only = "Colaborador,Data,Horas totais (decimal)\n".encode()
        with pytest.raises(ValueError, match="vazio"):
            _phase_load_and_validate(headers_only, "test.csv")

    def test_xlsx_file_accepted(self):
        buf = io.BytesIO()
        df_in = pd.DataFrame([BASE_ROW])
        df_in.to_excel(buf, index=False)
        df = _phase_load_and_validate(buf.getvalue(), "dados.xlsx")
        assert len(df) == 1

    def test_multiple_rows_returned(self):
        row2 = {**BASE_ROW, "Colaborador": "Maria Souza"}
        data = _csv(BASE_ROW, row2)
        df = _phase_load_and_validate(data, "test.csv")
        assert len(df) == 2

    def test_column_names_stripped(self):
        # Columns with surrounding whitespace should be stripped
        csv_data = b" Colaborador , Data , Horas totais (decimal) \nJoao,01/01/2026,8.0\n"
        df = _phase_load_and_validate(csv_data, "test.csv")
        assert "Colaborador" in df.columns
        assert "Data" in df.columns


# ---------------------------------------------------------------------------
# Phase 0 (auth): _phase_authorize_peps
# ---------------------------------------------------------------------------

class TestPhaseAuthorizePeps:
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

    def _make_project(self, db_session, pep_wbs):
        p = Project(pep_wbs=pep_wbs, name=pep_wbs)
        db_session.add(p)
        db_session.flush()
        return p

    def test_admin_returns_df_unchanged_and_no_warnings(self, db_session, sample_cycle):
        df = _df_from_rows(BASE_ROW)
        original_len = len(df)
        filtered_df, warnings = _phase_authorize_peps(df, db_session, None, "admin")
        assert len(filtered_df) == original_len
        assert warnings == []

    def test_user_without_acl_no_pep_column_passes(self, db_session, sample_cycle):
        """User with no ACL rows and no PEP column: no restriction applied."""
        row_no_pep = {k: v for k, v in BASE_ROW.items() if k != "Código PEP" and k != "PEP"}
        df = _df_from_rows(row_no_pep)
        user = self._make_user(db_session, "plain_user")
        db_session.commit()
        filtered_df, warnings = _phase_authorize_peps(df, db_session, user.id, "user")
        assert len(filtered_df) == len(df)
        assert warnings == []

    def test_user_with_acl_no_pep_column_raises_403(self, db_session, sample_cycle):
        """Non-admin with ACL rows but file lacks PEP column → 403."""
        from fastapi import HTTPException
        row_no_pep = {k: v for k, v in BASE_ROW.items() if k != "Código PEP" and k != "PEP"}
        df = _df_from_rows(row_no_pep)
        user = self._make_user(db_session, "acl_user")
        project = self._make_project(db_session, "60OP-001")
        db_session.add(UserProjectAccess(user_id=user.id, project_id=project.id))
        db_session.commit()
        with pytest.raises(HTTPException) as exc_info:
            _phase_authorize_peps(df, db_session, user.id, "user")
        assert exc_info.value.status_code == 403

    def test_no_access_to_any_pep_raises_403(self, db_session, sample_cycle):
        from fastapi import HTTPException
        user = self._make_user(db_session, "no_access_user")
        self._make_project(db_session, "60OP-001")
        db_session.commit()
        df = _df_from_rows(BASE_ROW)
        with pytest.raises(HTTPException) as exc_info:
            _phase_authorize_peps(df, db_session, user.id, "user")
        assert exc_info.value.status_code == 403
        assert "permissão" in exc_info.value.detail

    def test_partial_access_filters_unauthorized_rows(self, db_session, sample_cycle):
        user = self._make_user(db_session, "partial_user")
        proj_a = self._make_project(db_session, "60OP-001")
        db_session.add(UserProjectAccess(user_id=user.id, project_id=proj_a.id))
        self._make_project(db_session, "60OP-002")
        db_session.commit()

        row_b = {**BASE_ROW, "Código PEP": "60OP-002", "PEP": "Projeto Beta"}
        df = _df_from_rows(BASE_ROW, row_b)
        filtered_df, warnings = _phase_authorize_peps(df, db_session, user.id, "user")

        assert len(filtered_df) == 1
        assert "60OP-001" in filtered_df["Código PEP"].values
        assert any("permissão" in w for w in warnings)

    def test_no_pep_code_column_non_admin_no_acl_passes(self, db_session, sample_cycle):
        """Non-admin with no ACL rows and file has no PEP column: no restriction applied."""
        row_no_pep = {k: v for k, v in BASE_ROW.items() if k != "Código PEP" and k != "PEP"}
        df = _df_from_rows(row_no_pep)
        user = self._make_user(db_session, "open_user")
        db_session.commit()
        # No _COL_PEP_CODE column → pep_codes_raw is empty → no ACL check
        filtered_df, warnings = _phase_authorize_peps(df, db_session, user.id, "user")
        assert len(filtered_df) == len(df)
        assert warnings == []


# ---------------------------------------------------------------------------
# Phase 0b: _phase_prescan_dates
# ---------------------------------------------------------------------------

class TestPhasePrescanDates:
    def test_dates_with_active_cycle_cached(self, db_session, sample_cycle):
        df = _df_from_rows(BASE_ROW)  # date 15/01/2026 falls in sample_cycle
        cycle_cache = _phase_prescan_dates(df, db_session)
        d = date(2026, 1, 15)
        assert d in cycle_cache
        assert cycle_cache[d] is not None
        assert cycle_cache[d].id == sample_cycle.id

    def test_dates_without_cycle_cached_as_none(self, db_session):
        # No cycle registered in DB
        row = {**BASE_ROW, "Data": "15/01/2020"}
        df = _df_from_rows(row)
        cycle_cache = _phase_prescan_dates(df, db_session)
        d = date(2020, 1, 15)
        assert d in cycle_cache
        assert cycle_cache[d] is None

    def test_future_dates_not_cached(self, db_session):
        future = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
        row = {**BASE_ROW, "Data": future}
        df = _df_from_rows(row)
        cycle_cache = _phase_prescan_dates(df, db_session)
        # Future dates are excluded from pre-scan
        assert len(cycle_cache) == 0

    def test_invalid_dates_not_cached(self, db_session):
        row = {**BASE_ROW, "Data": "not-a-date"}
        df = _df_from_rows(row)
        cycle_cache = _phase_prescan_dates(df, db_session)
        assert len(cycle_cache) == 0

    def test_multiple_dates_multiple_cache_entries(self, db_session):
        cycle1 = _make_cycle(db_session, name="Jan/2026",
                              start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        cycle2 = _make_cycle(db_session, name="Feb/2026",
                              start_date=date(2026, 2, 1), end_date=date(2026, 2, 28))
        row1 = {**BASE_ROW, "Data": "15/01/2026"}
        row2 = {**BASE_ROW, "Data": "15/02/2026"}
        df = _df_from_rows(row1, row2)
        cycle_cache = _phase_prescan_dates(df, db_session)
        assert date(2026, 1, 15) in cycle_cache
        assert date(2026, 2, 15) in cycle_cache
        assert cycle_cache[date(2026, 1, 15)].id == cycle1.id
        assert cycle_cache[date(2026, 2, 15)].id == cycle2.id


# ---------------------------------------------------------------------------
# Phase 1+2: _phase_validate_rows
# ---------------------------------------------------------------------------

class TestPhaseValidateRows:
    def test_valid_row_passes_through(self, db_session, sample_cycle):
        df = _df_from_rows(BASE_ROW)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(valid_rows) == 1
        assert len(quarantine_buffer) == 0
        assert skipped == 0
        assert "João Silva" in new_collabs

    def test_q8_invalid_collaborator_name_quarantined(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Colaborador": "nan"}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(valid_rows) == 0
        assert len(quarantine_buffer) == 1
        assert "inválido" in quarantine_buffer[0]["reason"]
        assert skipped == 0

    def test_q8_single_char_name_quarantined(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Colaborador": "X"}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert len(valid_rows) == 0

    def test_q1_invalid_date_quarantined(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Data": "not-a-date"}
        df = _df_from_rows(row)
        cycle_cache: dict = {}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert "Data inválida" in quarantine_buffer[0]["reason"]

    def test_q2_future_date_quarantined(self, db_session, sample_cycle):
        future = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
        row = {**BASE_ROW, "Data": future}
        df = _df_from_rows(row)
        cycle_cache: dict = {}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert "futura" in quarantine_buffer[0]["reason"]

    def test_no_cycle_for_date_quarantined(self, db_session):
        # No cycle registered → cycle_cache maps the date to None
        row = {**BASE_ROW, "Data": "15/01/2020"}
        df = _df_from_rows(row)
        cycle_cache = {date(2020, 1, 15): None}  # pre-scanned as missing
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert "ciclo" in quarantine_buffer[0]["reason"].lower()

    def test_invalid_hours_quarantined(self, db_session, sample_cycle):
        row = {**BASE_ROW, "Horas totais (decimal)": "—"}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert "Horas inválidas" in quarantine_buffer[0]["reason"]

    def test_negative_hours_quarantined_by_rule(self, db_session, sample_cycle):
        # System rule: horas_individuais < 0 → quarentena
        row = {**BASE_ROW, "Horas totais (decimal)": -3.0}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert len(valid_rows) == 0

    def test_excess_hours_quarantined_by_rule(self, db_session, sample_cycle):
        # System rule: horas_individuais > 24 → quarentena
        row = {**BASE_ROW, "Horas totais (decimal)": 25.0}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(quarantine_buffer) == 1
        assert len(valid_rows) == 0

    def test_descarte_rule_increments_skipped(self, db_session, sample_cycle):
        rule = ValidationRule(
            is_system=False, is_active=True, order=50,
            field="horas_individuais", operator="gt", value="4",
            action="descarte", description="Test descarte",
        )
        db_session.add(rule)
        db_session.commit()

        row = {**BASE_ROW, "Horas totais (decimal)": 5.0}
        df = _df_from_rows(row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert skipped == 1
        assert len(valid_rows) == 0
        assert len(quarantine_buffer) == 0

    def test_existing_collaborator_not_re_added(self, db_session, sample_cycle):
        # Pre-seed the collaborator
        collab = _make_collaborator(db_session, "João Silva")

        df = _df_from_rows(BASE_ROW)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert "João Silva" not in new_collabs
        assert collab_cache["João Silva"].id == collab.id

    def test_multiple_rows_mixed_valid_and_quarantine(self, db_session, sample_cycle):
        good_row = BASE_ROW
        bad_row = {**BASE_ROW, "Colaborador": "nan"}
        df = _df_from_rows(good_row, bad_row)
        cycle_cache = {date(2026, 1, 15): sample_cycle}
        collab_cache: dict = {}
        rules = _rules(db_session)

        valid_rows, quarantine_buffer, warnings, infos, new_collabs, skipped = (
            _phase_validate_rows(df, db_session, rules, cycle_cache, collab_cache)
        )

        assert len(valid_rows) == 1
        assert len(quarantine_buffer) == 1


# ---------------------------------------------------------------------------
# Phase 3: _phase_aggregate_rules
# ---------------------------------------------------------------------------

class TestPhaseAggregateRules:
    def _make_valid_row(self, db_session, sample_cycle, collab_name="João Silva",
                        record_date=None, total_h=8.0):
        record_date = record_date or date(2026, 1, 15)
        collab = (
            db_session.query(Collaborator).filter_by(name=collab_name).first()
            or _make_collaborator(db_session, collab_name)
        )
        return {
            "row_idx": 2,
            "collab": collab,
            "record_date": record_date,
            "cycle": sample_cycle,
            "total_h": total_h,
            "row": pd.Series(BASE_ROW),
        }

    def test_no_rules_no_warnings(self, db_session, sample_cycle):
        # With only system rules (daily > 24 → warning), normal hours should pass
        valid_rows = [self._make_valid_row(db_session, sample_cycle, total_h=8.0)]
        rules = _rules(db_session)
        warnings, infos = _phase_aggregate_rules(valid_rows, rules)
        assert warnings == []

    def test_daily_sum_over_24_emits_warning(self, db_session, sample_cycle):
        # Two rows same collaborator same day totalling 25h triggers the system rule
        row1 = self._make_valid_row(db_session, sample_cycle, total_h=13.0)
        row2 = self._make_valid_row(db_session, sample_cycle, total_h=13.0)
        rules = _rules(db_session)
        warnings, infos = _phase_aggregate_rules([row1, row2], rules)
        assert any("Daily total" in w or "24" in w for w in warnings)

    def test_weekly_sum_over_60_emits_warning(self, db_session, sample_cycle):
        # Create rows across different days in the same ISO week to exceed 60h
        # ISO week 3 of 2026 covers Jan 12–18
        days_in_week = [date(2026, 1, 12), date(2026, 1, 13), date(2026, 1, 14),
                        date(2026, 1, 15), date(2026, 1, 16)]
        # Each row = 13h → 5 * 13 = 65h total (weekly sum > 60)
        valid_rows = [
            self._make_valid_row(db_session, sample_cycle, record_date=d, total_h=13.0)
            for d in days_in_week
        ]
        rules = _rules(db_session)
        warnings, infos = _phase_aggregate_rules(valid_rows, rules)
        assert any("60" in w or "Weekly" in w or "semanal" in w.lower() for w in warnings)

    def test_empty_valid_rows_no_output(self, db_session, sample_cycle):
        rules = _rules(db_session)
        warnings, infos = _phase_aggregate_rules([], rules)
        assert warnings == []
        assert infos == []

    def test_empty_rules_no_output(self, db_session, sample_cycle):
        valid_rows = [self._make_valid_row(db_session, sample_cycle, total_h=30.0)]
        warnings, infos = _phase_aggregate_rules(valid_rows, [])
        assert warnings == []
        assert infos == []

    def test_warning_includes_collaborator_and_date(self, db_session, sample_cycle):
        # Exceed daily threshold to ensure a warning is produced
        row1 = self._make_valid_row(db_session, sample_cycle, total_h=13.0)
        row2 = self._make_valid_row(db_session, sample_cycle, total_h=13.0)
        rules = _rules(db_session)
        warnings, infos = _phase_aggregate_rules([row1, row2], rules)
        # At least one warning must mention the collaborator name
        assert any("João Silva" in w for w in warnings)


# ---------------------------------------------------------------------------
# Phase 4: _phase_upsert_records
# ---------------------------------------------------------------------------

class TestPhaseUpsertRecords:
    def _make_valid_row_dict(self, db_session, sample_cycle, collab_name="João Silva",
                             record_date=None, total_h=8.0, pep_code="60OP-001",
                             row_idx=2, is_extra=False, is_standby=False):
        record_date = record_date or date(2026, 1, 15)
        collab = (
            db_session.query(Collaborator).filter_by(name=collab_name).first()
            or _make_collaborator(db_session, collab_name)
        )
        row_data = {
            **BASE_ROW,
            "Colaborador": collab_name,
            "Horas totais (decimal)": total_h,
            "Hora extra": "Sim" if is_extra else "Não",
            "Hora sobreaviso": "Sim" if is_standby else "Não",
        }
        if pep_code is None:
            row_data.pop("Código PEP", None)
            row_data.pop("PEP", None)
        else:
            row_data["Código PEP"] = pep_code
        return {
            "row_idx": row_idx,
            "collab": collab,
            "record_date": record_date,
            "cycle": sample_cycle,
            "total_h": total_h,
            "row": pd.Series(row_data),
        }

    def test_inserts_one_record(self, db_session, sample_cycle):
        vr = self._make_valid_row_dict(db_session, sample_cycle)
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr], 1.5, 0.33
        )
        db_session.flush()
        assert inserted == 1
        assert skipped == 0
        assert db_session.query(TimesheetRecord).count() == 1

    def test_zero_hours_row_skipped_not_inserted(self, db_session, sample_cycle):
        vr = self._make_valid_row_dict(db_session, sample_cycle, total_h=0.0)
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr], 1.5, 0.33
        )
        assert inserted == 0
        assert skipped == 1
        assert db_session.query(TimesheetRecord).count() == 0

    def test_duplicate_key_skipped(self, db_session, sample_cycle):
        vr1 = self._make_valid_row_dict(db_session, sample_cycle)
        vr2 = self._make_valid_row_dict(db_session, sample_cycle, row_idx=3)
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr1, vr2], 1.5, 0.33
        )
        db_session.flush()
        assert inserted == 1
        assert skipped == 1

    def test_extra_and_standby_conflict_warns_and_uses_extra(self, db_session, sample_cycle):
        vr = self._make_valid_row_dict(db_session, sample_cycle,
                                       is_extra=True, is_standby=True)
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr], 1.5, 0.33
        )
        db_session.flush()
        assert inserted == 1
        assert any("Sobreaviso simultaneamente" in w for w in warnings)
        record = db_session.query(TimesheetRecord).first()
        assert record.extra_hours == 8.0
        assert record.standby_hours == 0.0

    def test_zero_rate_warning_emitted_once(self, db_session, sample_cycle):
        # Collaborator with no seniority → rate=0 → warning
        vr1 = self._make_valid_row_dict(db_session, sample_cycle)
        vr2 = self._make_valid_row_dict(db_session, sample_cycle,
                                        record_date=date(2026, 1, 16), row_idx=3)
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr1, vr2], 1.5, 0.33
        )
        rate_warnings = [w for w in warnings if "sem taxa" in w]
        assert len(rate_warnings) == 1

    def test_pep_cycle_scope_populated(self, db_session, sample_cycle):
        vr = self._make_valid_row_dict(db_session, sample_cycle, pep_code="60OP-001")
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr], 1.5, 0.33
        )
        assert ("60OP-001", sample_cycle.id) in scope

    def test_surgical_delete_removes_old_records_for_same_pep_cycle(
        self, db_session, sample_cycle
    ):
        # Insert an existing record for the same (pep_wbs, cycle) via a direct ORM add
        collab = _make_collaborator(db_session, "Old Worker")
        db_session.add(TimesheetRecord(
            collaborator_id=collab.id,
            cycle_id=sample_cycle.id,
            record_date=date(2026, 1, 10),
            pep_wbs="60OP-001",
            normal_hours=4.0,
            extra_hours=0.0,
            standby_hours=0.0,
        ))
        db_session.commit()
        assert db_session.query(TimesheetRecord).count() == 1

        # Phase 4 should delete the old record and insert the new one
        vr = self._make_valid_row_dict(db_session, sample_cycle, pep_code="60OP-001")
        inserted, skipped, warnings, infos, scope = _phase_upsert_records(
            db_session, [vr], 1.5, 0.33
        )
        db_session.flush()
        # Old record gone, new one inserted
        assert db_session.query(TimesheetRecord).count() == 1
        record = db_session.query(TimesheetRecord).first()
        assert record.record_date == date(2026, 1, 15)
