from __future__ import annotations

import logging
from functools import lru_cache
import math
import re
import unicodedata
from datetime import date, timedelta
from io import BytesIO, StringIO

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.audit import log_audit
from backend.app.models import (
    Collaborator,
    Cycle,
    GlobalConfig,
    Project,
    RateCard,
    TimesheetRecord,
    UserProjectAccess,
    ValidationRule,
)
from backend.app.services.evm import freeze_costs
from backend.app.services.quarantine_svc import create_quarantine_record
from backend.app.services.rule_engine import evaluate_aggregate_rules, evaluate_row_rules
from backend.app.services.summaries import refresh_collaborator_cycle, refresh_pep_cycle
from backend.app.services.upload_session_svc import create_upload_session
from backend.app.utils import _str_or_none

log = logging.getLogger(__name__)

_COL_COLLABORATOR = "Colaborador"
_COL_DATE = "Data"
_COL_HOURS = "Horas totais (decimal)"
_COL_EXTRA = "Hora extra"
_COL_STANDBY = "Hora sobreaviso"
_COL_PEP_CODE = "Código PEP"
_COL_PEP_DESC = "PEP"
_COL_START_TIME = "Hora Inicial [H]"

_INVALID_COLLAB_NAMES = {"nan", "none", "unnamed", "0", "", "-", "—"}
_MAX_ROWS_WARNING = 5_000
_YEAR_FIRST = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}")
_PLAIN_DECIMAL = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)$")


class ClosedCycleError(Exception):
    def __init__(self, cycle_names: list[str]) -> None:
        self.cycle_names = cycle_names
        super().__init__(f"Ciclos fechados: {', '.join(cycle_names)}")


class LockedProjectError(Exception):
    def __init__(self, project_names: list[str]) -> None:
        self.project_names = project_names
        super().__init__(f"Projetos encerrados/suspensos: {', '.join(project_names)}")


class ArchivedCycleError(Exception):
    def __init__(self, cycle_names: list[str]) -> None:
        self.cycle_names = cycle_names
        super().__init__(f"Datas fora de ciclos ativos: {', '.join(cycle_names)}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ingest_file(
    file_bytes: bytes,
    filename: str,
    db: Session,
    user_role: str = "admin",
    user_id: int | None = None,
    username: str = "system",
    current_user=None,
) -> dict:
    # Phase 0: Load and validate structure
    df = _phase_load_and_validate(file_bytes, filename)

    # Authorization filter (Phase 0 — read-only, outside transaction)
    df, ingest_warnings = _phase_authorize_peps(df, db, user_id, user_role)
    acl_discarded = int(df.attrs.get("acl_discarded", 0))

    ingest_infos: list[str] = []

    if len(df) > _MAX_ROWS_WARNING:
        ingest_warnings.append(
            f"Arquivo com volume elevado: {len(df)} linhas. "
            f"Verifique se o período exportado está correto."
        )

    # Load active ValidationRules once for the entire ingest
    rules = (
        db.query(ValidationRule)
        .filter(ValidationRule.is_active == True)  # noqa: E712
        .order_by(ValidationRule.order)
        .all()
    )

    # Phase 0b: pre-scan all unique parseable dates
    collab_cache: dict[str, Collaborator] = {}
    cycle_cache = _phase_prescan_dates(df, db)

    # Phase 1 + 2: Per-row structural validation and rule evaluation
    valid_rows, quarantine_buffer, row_warnings, row_infos, new_collaborators, skipped = (
        _phase_validate_rows(df, db, rules, cycle_cache, collab_cache)
    )
    ingest_warnings.extend(row_warnings)
    ingest_infos.extend(row_infos)

    # N1: new collaborators info
    if new_collaborators:
        ingest_infos.append(
            f"Novo(s) colaborador(es) criado(s): {', '.join(new_collaborators)}."
        )
        ingest_infos.extend(_similar_collaborator_infos(db, new_collaborators))

    # RBAC check on valid rows' cycles
    if user_role != "admin":
        closed_names: list[str] = []
        seen_cycle_ids: set[int] = set()
        for vr in valid_rows:
            c = vr["cycle"]
            if c.id not in seen_cycle_ids and c.is_closed:
                closed_names.append(c.name)
            seen_cycle_ids.add(c.id)
        if closed_names:
            raise ClosedCycleError(closed_names)

    # Locked project check
    pep_codes_in_file: set[str] = {
        _str_or_none(vr["row"].get(_COL_PEP_CODE))
        for vr in valid_rows
    } - {None}
    if pep_codes_in_file:
        locked = (
            db.query(Project)
            .filter(
                Project.pep_wbs.in_(pep_codes_in_file),
                Project.status.in_(["encerrado", "suspenso"]),
            )
            .all()
        )
        if locked:
            raise LockedProjectError([p.name or p.pep_wbs for p in locked])

    # Phase 3: Aggregate rules — compute daily/weekly sums and evaluate
    agg_warnings, agg_infos = _phase_aggregate_rules(valid_rows, rules)
    ingest_warnings.extend(agg_warnings)
    ingest_infos.extend(agg_infos)

    # Load GlobalConfig multipliers once — used for freeze_costs
    cfg = db.get(GlobalConfig, 1)
    extra_multiplier   = cfg.extra_hours_multiplier   if cfg else 1.5
    standby_multiplier = cfg.standby_hours_multiplier if cfg else 0.33

    try:
        # Phase 4: Surgical DELETE by (pep_wbs, cycle_id) + INSERT fresh records
        replaced_collab_ids: set[int] = set()
        inserted, skipped_phase4, phase4_warnings, phase4_infos, pep_cycle_scope = (
            _phase_upsert_records(
                db, valid_rows, extra_multiplier, standby_multiplier,
                replaced_collab_ids=replaced_collab_ids,
            )
        )
        skipped += skipped_phase4 + acl_discarded
        ingest_warnings.extend(phase4_warnings)
        ingest_infos.extend(phase4_infos)

        # Refresh pre-computed summary tables for the affected (pep, cycle) pairs
        touched_peps    = list({pep for pep, _ in pep_cycle_scope})
        touched_cycles  = list({cid for _, cid in pep_cycle_scope})
        # Collaborators whose rows the surgical delete removed must be refreshed
        # too, otherwise their summary keeps stale hours.
        touched_collabs = list({vr["collab"].id for vr in valid_rows} | replaced_collab_ids)
        db.flush()  # make inserted records visible to summary queries
        refresh_pep_cycle(db, touched_peps, touched_cycles)
        refresh_collaborator_cycle(db, touched_collabs, touched_cycles)

        # Phase 5: QuarantineRecords + UploadSession + commit
        upload_session = create_upload_session(
            db,
            user_id=user_id,
            username=username,
            source_file=filename,
            status=("quarantine" if quarantine_buffer else "warnings" if ingest_warnings else "ok"),
            inserted=inserted,
            skipped=skipped,
            quarantine=len(quarantine_buffer),
            warning_count=len(ingest_warnings),
            info_count=len(ingest_infos),
            warnings=ingest_warnings,
            infos=ingest_infos,
        )

        for qr_data in quarantine_buffer:
            create_quarantine_record(
                db,
                upload_session_id=upload_session.id,
                user_id=user_id,
                username=username,
                raw_data=qr_data["raw_data"],
                reason=qr_data["reason"],
                rule_id=qr_data.get("rule_id"),
            )

        # Phase 6: AuditLog — inside the same transaction so data + audit are atomic
        _status = (
            "quarantine" if quarantine_buffer
            else "warnings" if ingest_warnings
            else "ok"
        )
        if current_user is not None:
            log_audit(db, current_user, "import", "timesheet", detail={
                "file": filename,
                "status": _status,
                "records_inserted": inserted,
                "records_skipped": skipped,
                "quarantine_records_added": len(quarantine_buffer),
            })

        session_id = upload_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    log.info(
        "Ingestão concluída: %d inseridos, %d duplicatas, %d quarentenas.",
        inserted, skipped, len(quarantine_buffer),
    )

    return {
        "status": _status,
        "records_inserted": inserted,
        "records_skipped": skipped,
        "records_summed": _merge_valid_rows(valid_rows)["n_summed"],
        "quarantine_records_added": len(quarantine_buffer),
        "warning_count": len(ingest_warnings),
        "info_count": len(ingest_infos),
        "warnings": ingest_warnings,
        "infos": ingest_infos,
        "upload_session_id": session_id,
        "affected_peps": sorted(pep_codes_in_file),
    }


# ---------------------------------------------------------------------------
# Phase functions — extracted from ingest_file() for independent testability
# ---------------------------------------------------------------------------


def _phase_load_and_validate(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Phase 0: Load file bytes into a DataFrame and validate required columns.

    Returns the validated DataFrame.
    Raises ValueError for missing required columns or empty file.
    """
    return _load_dataframe(file_bytes, filename)


def _phase_authorize_peps(
    df: pd.DataFrame,
    db: Session,
    user_id: int | None,
    user_role: str,
) -> tuple[pd.DataFrame, list[str]]:
    """Phase 0 (authorization): Filter DataFrame rows by user's PEP ACL.

    Returns (filtered_df, warnings).
    Raises HTTPException(403) when user has no access to any PEP in the file.
    """
    warnings: list[str] = []

    has_acl = False
    if user_role != "admin" and user_id is not None:
        has_acl = (
            db.query(UserProjectAccess)
            .filter(UserProjectAccess.user_id == user_id)
            .first()
        ) is not None

    # Non-admin with ACL restrictions must supply a PEP column.
    if has_acl and _COL_PEP_CODE not in df.columns:
        raise HTTPException(
            status_code=403,
            detail=(
                "Seu perfil possui restrições de acesso por PEP, mas o arquivo "
                "não contém a coluna 'Código PEP'. Inclua essa coluna no export "
                "ou solicite ao administrador acesso irrestrito."
            ),
        )

    pep_codes_raw: set[str] = set()
    if _COL_PEP_CODE in df.columns:
        pep_codes_raw = {_str_or_none(v) for v in df[_COL_PEP_CODE]} - {None}

    n_acl_discarded = 0

    # A user with a PEP whitelist may not import rows without a PEP code.
    if has_acl and _COL_PEP_CODE in df.columns:
        blank_mask = df[_COL_PEP_CODE].apply(lambda v: _str_or_none(v) is None)
        n_blank = int(blank_mask.sum())
        if n_blank:
            if n_blank == len(df):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Acesso negado: seu perfil possui restrições de acesso por PEP "
                        "e nenhuma linha do arquivo informa o 'Código PEP'."
                    ),
                )
            df = df[~blank_mask].copy()
            n_acl_discarded += n_blank
            warnings.append(
                f"{n_blank} linha(s) descartadas — sem PEP informado (seu perfil "
                f"só pode importar PEPs autorizados)."
            )

    if pep_codes_raw and user_id is not None:
        authorized = _authorized_peps(db, user_id, user_role, pep_codes_raw)
        if not authorized:
            top5 = sorted(pep_codes_raw)[:5]
            extra = f" e mais {len(pep_codes_raw) - 5}" if len(pep_codes_raw) > 5 else ""
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Acesso negado: seu perfil não tem permissão para importar "
                    f"nenhum dos PEPs encontrados neste arquivo "
                    f"({', '.join(top5)}{extra}). "
                    f"Solicite ao administrador que conceda acesso aos PEPs necessários."
                ),
            )
        unauthorized = pep_codes_raw - authorized
        if unauthorized:
            mask = df[_COL_PEP_CODE].apply(lambda v: _str_or_none(v) not in unauthorized)
            n_discarded = int((~mask).sum())
            n_acl_discarded += n_discarded
            df = df[mask].copy()
            top = sorted(unauthorized)[:5]
            suffix = f" e {len(unauthorized) - 5} outros." if len(unauthorized) > 5 else "."
            warnings.append(
                f"{n_discarded} linha(s) descartadas — sem permissão nos PEPs: "
                f"{', '.join(top)}{suffix}"
            )

    df.attrs["acl_discarded"] = n_acl_discarded
    return df, warnings


def _phase_prescan_dates(
    df: pd.DataFrame,
    db: Session,
) -> dict[date, "Cycle | None"]:
    """Phase 0b: Pre-scan all unique parseable past dates in the DataFrame.

    Returns a cycle_cache mapping each unique past date to its active Cycle
    (or None if no active cycle covers that date).
    """
    cycle_cache: dict[date, Cycle | None] = {}
    _today = date.today()
    _unique_dates: set[date] = set()

    for v in df[_COL_DATE]:
        d = _parse_date_safe(v)
        if d is not None and d <= _today:
            _unique_dates.add(d)

    for d in sorted(_unique_dates):
        try:
            cycle_cache[d] = _resolve_cycle(db, d)
        except ArchivedCycleError:
            cycle_cache[d] = None  # quarantined individually in Phase 1d

    return cycle_cache


def _phase_validate_rows(
    df: pd.DataFrame,
    db: Session,
    rules: list,
    cycle_cache: dict,
    collab_cache: dict,
) -> tuple[list[dict], list[dict], list[str], list[str], list[str], int]:
    """Phase 1+2: Per-row structural validation and rule evaluation.

    Returns (valid_rows, quarantine_buffer, warnings, infos, new_collaborators, skipped).
    Mutates collab_cache in place (adds newly resolved collaborators).
    """
    quarantine_buffer: list[dict] = []
    valid_rows: list[dict] = []
    warnings: list[str] = []
    infos: list[str] = []
    new_collaborators: list[str] = []
    skipped = 0
    legacy_names: dict[str, Collaborator] | None = None  # built once, on first new name

    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        name = _normalize_name(row[_COL_COLLABORATOR])

        # Phase 1a (Q8): collaborator name validation → quarantine
        if len(name) < 2 or name.lower() in _INVALID_COLLAB_NAMES:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Nome de colaborador inválido: '{row[_COL_COLLABORATOR]}'. Verifique a coluna 'Colaborador' no arquivo de origem e corrija.",
                "rule_id": None,
            })
            continue

        if name not in collab_cache:
            if legacy_names is None:
                legacy_names = _legacy_name_index(db)
            collab, created = _get_or_create_collaborator(db, name, legacy_names)
            collab_cache[name] = collab
            if created:
                new_collaborators.append(name)
        collab = collab_cache[name]

        # Phase 1b: date validation (Q1)
        record_date = _parse_date_safe(row[_COL_DATE])
        if record_date is None:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Data inválida: '{row[_COL_DATE]}'. Use o formato DD/MM/AAAA na coluna 'Data'.",
                "rule_id": None,
            })
            continue

        # Phase 1c (Q2): future date → quarantine
        if record_date > date.today():
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Data futura ({record_date}): registros com data posterior a hoje não são aceitos. Corrija no arquivo de origem.",
                "rule_id": None,
            })
            continue

        # Phase 1d: active cycle check — no cycle → quarantine row (not abort)
        if record_date not in cycle_cache:
            try:
                cycle_cache[record_date] = _resolve_cycle(db, record_date)
            except ArchivedCycleError:
                cycle_cache[record_date] = None
        cycle = cycle_cache[record_date]
        if cycle is None:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Nenhum ciclo ativo cobre a data {record_date} (colaborador: {name}). Cadastre o ciclo correspondente ou ajuste a data no arquivo de origem.",
                "rule_id": None,
            })
            continue

        # Phase 1e: hours parsing
        total_h = _safe_hours(row[_COL_HOURS])
        if total_h is None:
            if _str_or_none(row[_COL_HOURS]) is None:
                reason = (
                    "Horas ausentes: a célula da coluna 'Horas totais (decimal)' está vazia. "
                    "Preencha o valor no arquivo de origem."
                )
            else:
                reason = (
                    f"Horas inválidas ou ausentes: '{row[_COL_HOURS]}'. A coluna "
                    f"'Horas totais (decimal)' deve conter um número (ex.: 8.5). "
                    f"Corrija no arquivo de origem."
                )
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": reason,
                "rule_id": None,
            })
            continue

        pep_code = _str_or_none(row.get(_COL_PEP_CODE))

        # Phase 2: ValidationRule per-row evaluation
        row_fields = {
            "horas_individuais":    total_h,
            "pep_wbs":              pep_code,
            "dia_semana":           record_date.weekday(),
            "hora_extra":           _str_or_none(row.get(_COL_EXTRA)),
            "hora_sobreaviso":      _str_or_none(row.get(_COL_STANDBY)),
            "hora_extra_horas":     total_h if _is_yes(row.get(_COL_EXTRA, ""))    else 0.0,
            "hora_sobreaviso_horas": total_h if _is_yes(row.get(_COL_STANDBY, "")) else 0.0,
        }
        result = evaluate_row_rules(rules, row_fields)

        if result.final_action == "descarte":
            skipped += 1
            continue
        if result.final_action == "quarentena":
            rule_id = result.matches[-1].rule_id if result.matches else None
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": result.reason,
                "rule_id": rule_id,
            })
            continue

        if result.final_action == "warning":
            warnings.append(f"{result.reason} [{name}, {record_date}]")
        elif result.final_action == "info":
            infos.append(f"{result.reason} [{name}, {record_date}]")

        valid_rows.append({
            "row_idx": row_idx,
            "collab": collab,
            "record_date": record_date,
            "cycle": cycle,
            "total_h": total_h,
            "row": row,
        })

    return valid_rows, quarantine_buffer, warnings, infos, new_collaborators, skipped


_MAX_LISTED = 10  # cap on example lines in infos so a big file stays small


def _hour_type_of(row) -> str:
    is_extra = _is_yes(row.get(_COL_EXTRA, ""))
    is_standby = _is_yes(row.get(_COL_STANDBY, ""))
    return "extra" if is_extra else "standby" if is_standby else "normal"


def _fmt_h(h: float) -> str:
    return f"{h:.2f}".replace(".", ",") + " h"


def _merge_valid_rows(valid_rows: list[dict]) -> dict:
    """Collapse valid rows into the records that will be stored.

    Rows with the same key (collaborator, cycle, date, PEP, description, hour
    type, start time) are SUMMED when their hours differ. A row whose hours
    equal a row already seen under the same key is an exact duplicate and is
    discarded. Zero-hour rows are discarded.

    Returns {"merged", "n_summed", "n_dups", "n_zero", "sum_infos",
    "dup_infos", "warnings"}. Each merged item is the first row's dict with
    `total_h` summed, plus `hour_type` and `parts`.
    """
    groups: dict[tuple, dict] = {}
    order: list[dict] = []
    dup_lines: list[str] = []
    warnings: list[str] = []
    n_zero = 0
    n_dups = 0

    for vr in valid_rows:
        total_h = vr["total_h"]
        if total_h == 0.0:
            n_zero += 1
            continue
        row = vr["row"]
        collab = vr["collab"]
        record_date = vr["record_date"]
        if _is_yes(row.get(_COL_EXTRA, "")) and _is_yes(row.get(_COL_STANDBY, "")):
            warnings.append(
                f"Linha {vr['row_idx']}: colaborador '{collab.name}' em {record_date} "
                f"marcado como Extra E Sobreaviso simultaneamente → classificado como Extra."
            )
        hour_type = _hour_type_of(row)
        pep_code = _str_or_none(row.get(_COL_PEP_CODE))
        key = (
            collab.id, vr["cycle"].id, record_date, pep_code,
            _str_or_none(row.get(_COL_PEP_DESC)), hour_type,
            _str_or_none(row.get(_COL_START_TIME)),
        )
        g = groups.get(key)
        if g is None:
            g = {**vr, "hour_type": hour_type, "parts": [total_h],
                 "_seen": {round(total_h, 6)}, "_pep": pep_code}
            groups[key] = g
            order.append(g)
            continue
        if round(total_h, 6) in g["_seen"]:
            n_dups += 1
            if len(dup_lines) < _MAX_LISTED:
                pep_label = f" | PEP {pep_code}" if pep_code else ""
                dup_lines.append(
                    f"Linha {vr['row_idx']}: duplicata ignorada — {collab.name} em "
                    f"{record_date}{pep_label} ({hour_type}, {total_h:.2f}h)"
                )
            continue
        g["_seen"].add(round(total_h, 6))
        g["parts"].append(total_h)
        g["total_h"] = g["total_h"] + total_h

    sum_examples: list[str] = []
    n_summed = 0
    for g in order:
        if len(g["parts"]) > 1:
            n_summed += len(g["parts"]) - 1
            label = f" | PEP {g['_pep']}" if g["_pep"] else ""
            sum_examples.append(
                f"{g['collab'].name} em {g['record_date'].strftime('%d/%m/%Y')}{label} "
                f"({' + '.join(_fmt_h(h) for h in g['parts'])} = {_fmt_h(g['total_h'])})"
            )
    sum_infos: list[str] = []
    if sum_examples:
        shown = sum_examples[:_MAX_LISTED]
        tail = (
            f"; +{len(sum_examples) - _MAX_LISTED} outras"
            if len(sum_examples) > _MAX_LISTED else ""
        )
        sum_infos.append(
            f"{n_summed} linha(s) do mesmo dia somada(s): {'; '.join(shown)}{tail}"
        )
    dup_infos = list(dup_lines)
    if n_dups > len(dup_lines):
        dup_infos.append(f"+{n_dups - len(dup_lines)} outras duplicatas ignoradas.")

    return {
        "merged": order, "n_summed": n_summed, "n_dups": n_dups, "n_zero": n_zero,
        "sum_infos": sum_infos, "dup_infos": dup_infos, "warnings": warnings,
    }


def _phase_aggregate_rules(
    valid_rows: list[dict],
    rules: list,
) -> tuple[list[str], list[str]]:
    """Phase 3: Compute daily/weekly sums and evaluate aggregate rules.

    Returns (warnings, infos).
    """
    warnings: list[str] = []
    infos: list[str] = []

    daily_sums: dict[tuple, float] = {}
    weekly_sums: dict[tuple, float] = {}
    week_first_day: dict[tuple, object] = {}  # (collab_name, (year, week)) → earliest date with data

    for vr in _merge_valid_rows(valid_rows)["merged"]:  # the hours that are stored
        collab_name = vr["collab"].name
        d = vr["record_date"]
        key_d = (collab_name, d)
        key_w = (collab_name, d.isocalendar()[:2])
        daily_sums[key_d] = daily_sums.get(key_d, 0.0) + vr["total_h"]
        weekly_sums[key_w] = weekly_sums.get(key_w, 0.0) + vr["total_h"]
        if key_w not in week_first_day or d < week_first_day[key_w]:
            week_first_day[key_w] = d

    # Daily rules — one evaluation per (collaborator, day)
    daily_rules = [r for r in rules if r.field == "soma_diaria"]
    for (collab_name, d), daily_total in daily_sums.items():
        for m in evaluate_aggregate_rules(daily_rules, daily_total, 0.0):
            (warnings if m.action == "warning" else infos).append(
                f"{collab_name} em {d}: {m.message}"
            )

    # Weekly rules — one evaluation per (collaborator, ISO week); date shown is
    # the earliest day with data in that week so the message points to a real entry.
    weekly_rules = [r for r in rules if r.field == "soma_semanal"]
    for (collab_name, key_w), weekly_total in weekly_sums.items():
        first_day = week_first_day[(collab_name, key_w)]
        for m in evaluate_aggregate_rules(weekly_rules, 0.0, weekly_total):
            (warnings if m.action == "warning" else infos).append(
                f"{collab_name} em {first_day}: {m.message}"
            )

    return warnings, infos


def _phase_upsert_records(
    db: Session,
    valid_rows: list[dict],
    extra_multiplier: float,
    standby_multiplier: float,
    replaced_collab_ids: set[int] | None = None,
) -> tuple[int, int, list[str], list[str], set[tuple]]:
    """Phase 4: Surgical DELETE by (pep_wbs, cycle_id) + INSERT fresh records.

    Returns (inserted, skipped, warnings, infos, pep_cycle_scope).
    When `replaced_collab_ids` is given, it receives the ids of every
    collaborator that had rows removed by the delete, so the caller can
    refresh their summaries.
    Does NOT commit — the caller owns the transaction.
    """
    warnings: list[str] = []
    infos: list[str] = []

    pep_cycle_scope: set[tuple[str | None, int]] = set()
    cycle_names: dict[int, str] = {}
    for vr in valid_rows:
        pep = _str_or_none(vr["row"].get(_COL_PEP_CODE))
        pep_cycle_scope.add((pep, vr["cycle"].id))
        cycle_names[vr["cycle"].id] = vr["cycle"].name

    # (label, cycle_id) -> number of previous rows deleted
    replaced: dict[tuple[str, int], int] = {}

    def _delete(label: str, cycle_id: int, query) -> None:
        collab_ids = {r[0] for r in query.with_entities(TimesheetRecord.collaborator_id).distinct()}
        n_deleted = query.delete(synchronize_session=False)
        if n_deleted:
            replaced[(label, cycle_id)] = replaced.get((label, cycle_id), 0) + n_deleted
            if replaced_collab_ids is not None:
                replaced_collab_ids.update(collab_ids)

    for scope_pep, cycle_id in sorted(pep_cycle_scope, key=lambda s: (s[0] or "", s[1])):
        if scope_pep is not None:
            _delete(
                f"PEP {scope_pep}", cycle_id,
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.pep_wbs == scope_pep,
                    TimesheetRecord.cycle_id == cycle_id,
                ),
            )

    null_by_cycle: dict[int, dict[int, str]] = {}
    for vr in valid_rows:
        if _str_or_none(vr["row"].get(_COL_PEP_CODE)) is None:
            null_by_cycle.setdefault(vr["cycle"].id, {})[vr["collab"].id] = vr["collab"].name
    for cycle_id, collabs in null_by_cycle.items():
        for collab_id, collab_name in collabs.items():
            _delete(
                f"sem PEP ({collab_name})", cycle_id,
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.collaborator_id == collab_id,
                    TimesheetRecord.cycle_id == cycle_id,
                    TimesheetRecord.pep_wbs.is_(None),
                ),
            )

    inserted_by_scope: dict[tuple[str, int], int] = {}

    mr = _merge_valid_rows(valid_rows)
    warnings.extend(mr["warnings"])
    infos.extend(mr["sum_infos"])
    infos.extend(mr["dup_infos"])
    # Rows folded into another record still count as inserted rows (their
    # hours are stored), so inserted + skipped + quarantined == rows in file.
    inserted = mr["n_summed"]
    skipped = mr["n_zero"] + mr["n_dups"]
    warned_zero_rate: set[str] = set()
    rate_cache: dict[tuple, float] = {}

    for vr in mr["merged"]:
        collab = vr["collab"]
        record_date = vr["record_date"]
        cycle = vr["cycle"]
        total_h = vr["total_h"]
        hour_type = vr["hour_type"]
        if hour_type == "extra":
            extra_h = total_h; normal_h = standby_h = 0.0
        elif hour_type == "standby":
            standby_h = total_h; normal_h = extra_h = 0.0
        else:
            normal_h = total_h; extra_h = standby_h = 0.0
        pep_code = vr["_pep"]
        pep_desc = _str_or_none(vr["row"].get(_COL_PEP_DESC))

        rkey = (collab.seniority_level_id, record_date)
        if rkey not in rate_cache:
            rate_cache[rkey] = _lookup_rate(db, collab, record_date)
        rate = rate_cache[rkey]
        if rate == 0.0 and collab.name not in warned_zero_rate:
            warnings.append(
                f"Colaborador '{collab.name}' sem taxa cadastrada para {record_date} "
                f"→ custo registrado como R$0,00."
            )
            warned_zero_rate.add(collab.name)

        nc, ec, sc = freeze_costs(
            normal_h, extra_h, standby_h,
            rate, extra_multiplier, standby_multiplier,
        )

        db.add(TimesheetRecord(
            collaborator_id=collab.id,
            cycle_id=cycle.id,
            record_date=record_date,
            pep_wbs=pep_code,
            pep_description=pep_desc,
            normal_hours=normal_h,
            extra_hours=extra_h,
            standby_hours=standby_h,
            cost_per_hour=rate,
            normal_cost=nc,
            extra_cost=ec,
            standby_cost=sc,
        ))
        inserted += 1
        label = f"PEP {pep_code}" if pep_code else f"sem PEP ({collab.name})"
        inserted_by_scope[(label, cycle.id)] = inserted_by_scope.get((label, cycle.id), 0) + 1

    # A file is a full export of its (PEP, cycle): say how much was replaced.
    for (label, cycle_id), n_old in sorted(replaced.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        n_new = inserted_by_scope.get((label, cycle_id), 0)
        infos.append(
            f"{label}, ciclo {cycle_names.get(cycle_id, cycle_id)}: "
            f"{n_old} registro(s) anterior(es) substituído(s) por {n_new}."
        )

    return inserted, skipped, warnings, infos, pep_cycle_scope


def ingest_csv(file_bytes: bytes, db: Session) -> dict:
    return ingest_file(file_bytes, "file.csv", db)


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------

def _authorized_peps(
    db: Session,
    user_id: int | None,
    user_role: str,
    pep_codes: set[str],
) -> set[str]:
    if user_role == "admin" or not pep_codes:
        return set(pep_codes)
    if user_id is None:
        return set()
    # Empty whitelist = access to all (same rule as the v2 analytics routes).
    has_rows = db.query(UserProjectAccess.id).filter(UserProjectAccess.user_id == user_id).first()
    if has_rows is None:
        return set(pep_codes)

    delegated: set[str] = {
        p.pep_wbs
        for p in db.query(Project)
        .join(UserProjectAccess, UserProjectAccess.project_id == Project.id)
        .filter(
            Project.pep_wbs.in_(pep_codes),
            UserProjectAccess.user_id == user_id,
        )
        .all()
    }

    return delegated


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


_CANONICAL_COLUMNS = (
    _COL_COLLABORATOR, _COL_DATE, _COL_HOURS, _COL_EXTRA, _COL_STANDBY,
    _COL_PEP_CODE, _COL_PEP_DESC, _COL_START_TIME,
)
_STRING_COLUMNS = (_COL_PEP_CODE, _COL_PEP_DESC)


def _column_key(name) -> str:
    """Case/whitespace-insensitive key used to match column names."""
    return " ".join(unicodedata.normalize("NFC", str(name)).split()).casefold()


def _canonical_column_map(columns) -> dict:
    """Map each file column to its canonical name (first match wins)."""
    by_key = {_column_key(c): c for c in _CANONICAL_COLUMNS}
    mapping: dict = {}
    used: set[str] = set()
    for col in columns:
        canon = by_key.get(_column_key(col))
        if canon is not None and canon not in used:
            mapping[col] = canon
            used.add(canon)
    return mapping


def _decode_csv(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return file_bytes.decode("cp1252")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _detect_delimiter(text: str) -> str:
    first = next((ln for ln in text.splitlines() if ln.strip()), "")
    return ";" if first.count(";") > first.count(",") else ","


def _clean_excel_code(value):
    """Remove the float artifact ('1001.0') that Excel numeric cells get as text."""
    if isinstance(value, str) and re.fullmatch(r"\d+\.0", value):
        return value[:-2]
    return value


def _load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if not file_bytes or not file_bytes.strip():
        raise ValueError("O arquivo está vazio. Exporte novamente o timesheet e tente de novo.")

    is_excel = filename.lower().endswith((".xlsx", ".xls"))
    try:
        if is_excel:
            header = pd.read_excel(BytesIO(file_bytes), nrows=0)
        else:
            text = _decode_csv(file_bytes)
            sep = _detect_delimiter(text)
            header = pd.read_csv(StringIO(text), sep=sep, nrows=0)
        # PEP code and description are identifiers: never let pandas infer numbers.
        str_cols = {
            col: str for col, canon in _canonical_column_map(header.columns).items()
            if canon in _STRING_COLUMNS
        }
        if is_excel:
            df = pd.read_excel(BytesIO(file_bytes), dtype=str_cols or None)
            for col in str_cols:
                df[col] = df[col].map(_clean_excel_code)
        else:
            df = pd.read_csv(StringIO(text), sep=sep, dtype=str_cols or None)
    except pd.errors.EmptyDataError:
        raise ValueError("O arquivo está vazio. Exporte novamente o timesheet e tente de novo.") from None
    except Exception as exc:
        if is_excel:
            raise ValueError(
                "Não foi possível ler o arquivo Excel. Verifique se ele não está "
                "corrompido e se está no formato .xlsx ou .xls."
            ) from exc
        raise ValueError(
            "Não foi possível ler o arquivo CSV. Verifique o separador (vírgula ou "
            "ponto e vírgula) e o formato das linhas."
        ) from exc

    df = df.rename(columns=_canonical_column_map(df.columns))
    df.columns = [str(c).strip() for c in df.columns]
    required = {_COL_COLLABORATOR, _COL_DATE, _COL_HOURS}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if df.empty:
        raise ValueError(
            "Arquivo vazio: contém apenas o cabeçalho, sem registros de horas. "
            "Verifique a exportação."
        )
    return df


def _normalize_name(value) -> str:
    """NFC + trim + collapse inner whitespace. Case and accents are kept."""
    return " ".join(unicodedata.normalize("NFC", str(value)).split())


def _name_key(name: str) -> str:
    """Casefolded, accent-stripped key used only to flag likely duplicates."""
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.split()).casefold()


def _similar_collaborator_infos(db: Session, new_names: list[str]) -> list[str]:
    """Info messages for new collaborators that look like an existing one."""
    by_key: dict[str, set[str]] = {}
    for (existing,) in db.query(Collaborator.name).all():
        by_key.setdefault(_name_key(existing), set()).add(existing)
    infos: list[str] = []
    for new in new_names:
        others = sorted(by_key.get(_name_key(new), set()) - {new})
        if others:
            quoted = ", ".join(f"'{o}'" for o in others)
            infos.append(
                f"Possível duplicidade: o colaborador novo '{new}' é semelhante a {quoted} "
                f"(difere só em maiúsculas/acentos). Verifique se são a mesma pessoa."
            )
    return infos


def _legacy_name_index(db: Session) -> dict[str, Collaborator]:
    """Normalized name -> collaborator, for rows stored un-normalized (NFD, double spaces)."""
    index: dict[str, Collaborator] = {}
    for existing in db.query(Collaborator).order_by(Collaborator.id).all():
        index.setdefault(_normalize_name(existing.name), existing)
    return index


def _get_or_create_collaborator(
    db: Session, name: str, legacy_names: dict[str, Collaborator] | None = None,
) -> tuple[Collaborator, bool]:
    name = _normalize_name(name)
    collab = db.query(Collaborator).filter(Collaborator.name == name).first()
    if collab is None:
        if legacy_names is None:
            legacy_names = _legacy_name_index(db)
        if name in legacy_names:
            return legacy_names[name], False
    if collab is None:
        collab = Collaborator(name=name)
        db.add(collab)
        db.flush()
        return collab, True
    return collab, False


def _resolve_cycle(db: Session, record_date: date) -> Cycle:
    cycle = (
        db.query(Cycle)
        .filter(
            Cycle.start_date <= record_date,
            Cycle.end_date >= record_date,
            Cycle.is_active == True,  # noqa: E712
        )
        .first()
    )
    if cycle is None:
        raise ArchivedCycleError([str(record_date)])
    return cycle


def _parse_date(value) -> date:
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value if type(value) is date else value.date()
    if isinstance(value, (int, float)):
        return date(1899, 12, 30) + timedelta(days=int(value))
    return _parse_date_text(str(value).strip())


@lru_cache(maxsize=8192)
def _parse_date_text(text: str) -> date:
    # A date that starts with a 4-digit year is year-first (ISO). Forcing day-first
    # on it swaps the day and the month (2026-01-05 would become 1 May 2026).
    # Cached: a file repeats a few dozen dates over thousands of rows.
    return pd.to_datetime(text, dayfirst=not _YEAR_FIRST.match(text)).date()


def _parse_date_safe(value) -> date | None:
    try:
        return _parse_date(value)
    except Exception:
        return None


def _is_yes(value) -> bool:
    return str(value).strip().lower() in {"sim", "yes", "s", "y", "true", "1"}




def _safe_hours(value) -> float | None:
    """Parse a cell value to a finite float of hours, or None if unparseable.

    Returns None for: None, empty/non-parseable text, NaN, Inf.
    Returns the float as-is for valid numbers (including negative and >24h),
    so that ValidationRules in Phase 2 can apply the correct action.
    """
    if value is None:
        return None

    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        # Real numeric cell (e.g. Excel): no text parsing, so 1e-05 stays valid.
        v = float(value)
    else:
        raw = str(value).strip().replace(",", ".")
        # Plain decimal only: no scientific notation, underscores, inf/nan words.
        if not _PLAIN_DECIMAL.match(raw):
            return None
        try:
            v = float(raw)
        except (ValueError, TypeError):
            return None

    if math.isnan(v) or math.isinf(v):
        return None

    return v


def _row_to_dict(row) -> dict:
    """Convert a pandas Series to a JSON-serializable dict."""
    d = {}
    for k, v in row.items():
        try:
            is_na = pd.isna(v)
        except (TypeError, ValueError):
            is_na = False
        if is_na or (isinstance(v, float) and math.isinf(v)):
            d[str(k)] = None
        elif hasattr(v, "item"):
            d[str(k)] = v.item()
        else:
            d[str(k)] = v if isinstance(v, (bool, int, float, str, type(None))) else str(v)
    return d


def _lookup_rate(db: Session, collab: Collaborator, record_date: date) -> float:
    if collab.seniority_level_id is None:
        return 0.0
    rc = (
        db.query(RateCard)
        .filter(
            RateCard.seniority_level_id == collab.seniority_level_id,
            RateCard.valid_from <= record_date,
            (RateCard.valid_to.is_(None)) | (RateCard.valid_to >= record_date),
        )
        .order_by(RateCard.valid_from.desc())
        .first()
    )
    return rc.hourly_rate if rc else 0.0
