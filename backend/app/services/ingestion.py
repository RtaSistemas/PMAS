from __future__ import annotations

import logging
import math
import re
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import (
    Collaborator,
    Cycle,
    Project,
    RateCard,
    TimesheetRecord,
    UserProjectAccess,
    ValidationRule,
)
from backend.app.services.quarantine_svc import create_quarantine_record
from backend.app.services.rule_engine import evaluate_aggregate_rules, evaluate_row_rules
from backend.app.services.upload_session_svc import create_upload_session

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
_PEP_PATTERN = re.compile(r"^[A-Z0-9]{2,}-[A-Z0-9]{3,}$", re.IGNORECASE)


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
) -> dict:
    # Phase 0: Load and validate structure
    df = _load_dataframe(file_bytes, filename)
    ingest_warnings: list[str] = []
    ingest_infos: list[str] = []

    # Authorization filter (read-only, outside transaction)
    pep_codes_raw: set[str] = set()
    if _COL_PEP_CODE in df.columns:
        pep_codes_raw = {_str_or_none(v) for v in df[_COL_PEP_CODE]} - {None}

    if pep_codes_raw and user_id is not None:
        authorized = _authorized_peps(db, user_id, user_role, pep_codes_raw)
        unauthorized = pep_codes_raw - authorized
        if unauthorized:
            mask = df[_COL_PEP_CODE].apply(lambda v: _str_or_none(v) not in unauthorized)
            n_discarded = int((~mask).sum())
            df = df[mask].copy()
            top = sorted(unauthorized)[:5]
            suffix = f" e {len(unauthorized) - 5} outros." if len(unauthorized) > 5 else "."
            ingest_warnings.append(
                f"{n_discarded} linha(s) descartadas — sem permissão nos PEPs: "
                f"{', '.join(top)}{suffix}"
            )

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

    # Phase 0b: pre-scan all unique parseable dates — if any has no active cycle
    # reject the entire file immediately (spec: rejeição total, Camada 1)
    collab_cache: dict[str, Collaborator] = {}
    cycle_cache: dict[date, Cycle | None] = {}
    quarantine_buffer: list[dict] = []
    valid_rows: list[dict] = []

    _today = date.today()
    _unique_dates: set[date] = set()
    for v in df[_COL_DATE]:
        d = _parse_date_safe(v)
        # Future dates are handled per-row (Q2); skip them in the pre-scan
        if d is not None and d <= _today:
            _unique_dates.add(d)

    _no_cycle_dates: list[str] = []
    for d in sorted(_unique_dates):
        try:
            cycle_cache[d] = _resolve_cycle(db, d)
        except ArchivedCycleError:
            _no_cycle_dates.append(str(d))

    if _no_cycle_dates:
        raise ArchivedCycleError(_no_cycle_dates)

    # Phase 1 + 2: Per-row structural validation and rule evaluation
    skipped = 0
    new_collaborators: list[str] = []

    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        name = str(row[_COL_COLLABORATOR]).strip()

        # Phase 1a (Q8): collaborator name validation → quarantine
        if len(name) < 2 or name.lower() in _INVALID_COLLAB_NAMES:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Nome de colaborador inválido: {row[_COL_COLLABORATOR]!r}",
                "rule_id": None,
            })
            continue

        if name not in collab_cache:
            collab, created = _get_or_create_collaborator(db, name)
            collab_cache[name] = collab
            if created:
                new_collaborators.append(name)
        collab = collab_cache[name]

        # Phase 1b: date validation (Q1)
        record_date = _parse_date_safe(row[_COL_DATE])
        if record_date is None:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Data inválida: {row[_COL_DATE]!r}",
                "rule_id": None,
            })
            continue

        # Phase 1c (Q2): future date → quarantine
        if record_date > date.today():
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Data futura: {record_date}",
                "rule_id": None,
            })
            continue

        # Phase 1d: active cycle check (raises ArchivedCycleError if none found)
        if record_date not in cycle_cache:
            cycle_cache[record_date] = _resolve_cycle(db, record_date)
        cycle = cycle_cache[record_date]

        # Phase 1e: hours parsing
        total_h = _safe_hours(row[_COL_HOURS])
        if total_h is None:
            quarantine_buffer.append({
                "raw_data": _row_to_dict(row),
                "reason": f"Horas inválidas ou ausentes: {row[_COL_HOURS]!r}",
                "rule_id": None,
            })
            continue

        pep_code = _str_or_none(row.get(_COL_PEP_CODE))

        # Phase 2: ValidationRule per-row evaluation
        row_fields = {
            "horas_individuais": total_h,
            "pep_wbs": pep_code,
            "dia_semana": record_date.weekday(),
            "hora_extra": _str_or_none(row.get(_COL_EXTRA)),
            "hora_sobreaviso": _str_or_none(row.get(_COL_STANDBY)),
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
            ingest_warnings.append(result.reason)
        elif result.final_action == "info":
            ingest_infos.append(result.reason)

        valid_rows.append({
            "row_idx": row_idx,
            "collab": collab,
            "record_date": record_date,
            "cycle": cycle,
            "total_h": total_h,
            "row": row,
        })

    # N1: new collaborators info
    if new_collaborators:
        ingest_infos.append(
            f"Novo(s) colaborador(es) criado(s): {', '.join(new_collaborators)}."
        )

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
    daily_sums: dict[tuple, float] = {}
    weekly_sums: dict[tuple, float] = {}
    for vr in valid_rows:
        collab_name = vr["collab"].name
        d = vr["record_date"]
        key_d = (collab_name, d)
        key_w = (collab_name, d.isocalendar()[:2])
        daily_sums[key_d] = daily_sums.get(key_d, 0.0) + vr["total_h"]
        weekly_sums[key_w] = weekly_sums.get(key_w, 0.0) + vr["total_h"]

    for (collab_name, d), daily_total in daily_sums.items():
        key_w = (collab_name, d.isocalendar()[:2])
        weekly_total = weekly_sums.get(key_w, 0.0)
        for m in evaluate_aggregate_rules(rules, daily_total, weekly_total):
            if m.action == "warning":
                ingest_warnings.append(f"{collab_name} em {d}: {m.message}")
            elif m.action == "info":
                ingest_infos.append(f"{collab_name} em {d}: {m.message}")

    try:
        # Phase 4: Surgical DELETE by (pep_wbs, cycle_id) + INSERT fresh records
        pep_cycle_scope: set[tuple[str | None, int]] = set()
        for vr in valid_rows:
            pep = _str_or_none(vr["row"].get(_COL_PEP_CODE))
            pep_cycle_scope.add((pep, vr["cycle"].id))

        for scope_pep, cycle_id in pep_cycle_scope:
            if scope_pep is not None:
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.pep_wbs == scope_pep,
                    TimesheetRecord.cycle_id == cycle_id,
                ).delete(synchronize_session=False)

        null_by_cycle: dict[int, set[int]] = {}
        for vr in valid_rows:
            if _str_or_none(vr["row"].get(_COL_PEP_CODE)) is None:
                null_by_cycle.setdefault(vr["cycle"].id, set()).add(vr["collab"].id)
        for cycle_id, collab_ids in null_by_cycle.items():
            for collab_id in collab_ids:
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.collaborator_id == collab_id,
                    TimesheetRecord.cycle_id == cycle_id,
                    TimesheetRecord.pep_wbs.is_(None),
                ).delete(synchronize_session=False)

        seen_keys: set[tuple] = set()
        inserted = 0
        warned_zero_rate: set[str] = set()

        for vr in valid_rows:
            collab = vr["collab"]
            record_date = vr["record_date"]
            cycle = vr["cycle"]
            total_h = vr["total_h"]
            row = vr["row"]
            row_idx = vr["row_idx"]

            if total_h == 0.0:
                skipped += 1
                continue

            is_extra = _is_yes(row.get(_COL_EXTRA, ""))
            is_standby = _is_yes(row.get(_COL_STANDBY, ""))

            if is_extra and is_standby:
                ingest_warnings.append(
                    f"Linha {row_idx}: colaborador '{collab.name}' em {record_date} "
                    f"marcado como Extra E Sobreaviso simultaneamente → classificado como Extra."
                )

            if is_extra:
                extra_h = total_h; normal_h = standby_h = 0.0; hour_type = "extra"
            elif is_standby:
                standby_h = total_h; normal_h = extra_h = 0.0; hour_type = "standby"
            else:
                normal_h = total_h; extra_h = standby_h = 0.0; hour_type = "normal"

            pep_code = _str_or_none(row.get(_COL_PEP_CODE))
            pep_desc = _str_or_none(row.get(_COL_PEP_DESC))
            start_time = _str_or_none(row.get(_COL_START_TIME))

            key = (collab.id, cycle.id, record_date, pep_code, pep_desc, hour_type, start_time)
            if key in seen_keys:
                skipped += 1
                continue
            seen_keys.add(key)

            rate = _lookup_rate(db, collab, record_date)
            if rate == 0.0 and collab.name not in warned_zero_rate:
                ingest_warnings.append(
                    f"Colaborador '{collab.name}' sem taxa cadastrada para {record_date} "
                    f"→ custo registrado como R$0,00."
                )
                warned_zero_rate.add(collab.name)

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
            ))
            inserted += 1

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

        session_id = upload_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Phase 6: audit (caller may also call log_audit after this returns)
    if quarantine_buffer:
        status = "quarantine"
    elif ingest_warnings:
        status = "warnings"
    else:
        status = "ok"

    log.info(
        "Ingestão concluída: %d inseridos, %d duplicatas, %d quarentenas.",
        inserted, skipped, len(quarantine_buffer),
    )

    return {
        "status": status,
        "records_inserted": inserted,
        "records_skipped": skipped,
        "quarantine_records_added": len(quarantine_buffer),
        "warning_count": len(ingest_warnings),
        "info_count": len(ingest_infos),
        "warnings": ingest_warnings,
        "infos": ingest_infos,
        "upload_session_id": session_id,
    }


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

    managed: set[str] = {
        p.pep_wbs
        for p in db.query(Project)
        .filter(Project.pep_wbs.in_(pep_codes), Project.manager_id == user_id)
        .all()
    }

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

    return managed | delegated


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        df = pd.read_csv(BytesIO(file_bytes))

    df.columns = [c.strip() for c in df.columns]
    required = {_COL_COLLABORATOR, _COL_DATE, _COL_HOURS}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")
    if df.empty:
        raise ValueError("Arquivo vazio ou sem registros.")
    return df


def _get_or_create_collaborator(db: Session, name: str) -> tuple[Collaborator, bool]:
    collab = db.query(Collaborator).filter(Collaborator.name == name).first()
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
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return date(1899, 12, 30) + timedelta(days=int(value))
    return pd.to_datetime(str(value), dayfirst=True).date()


def _parse_date_safe(value) -> date | None:
    try:
        return _parse_date(value)
    except Exception:
        return None


def _is_yes(value) -> bool:
    return str(value).strip().lower() in {"sim", "yes", "s", "y", "true", "1"}


def _str_or_none(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in {"nan", "none", ""} else s


def _safe_hours(value) -> float | None:
    """Parse a cell value to a finite float of hours, or None if unparseable.

    Returns None for: None, empty/non-parseable text, NaN, Inf.
    Returns the float as-is for valid numbers (including negative and >24h),
    so that ValidationRules in Phase 2 can apply the correct action.
    """
    if value is None:
        return None

    raw = str(value).strip().replace(",", ".")

    if raw == "" or raw.lower() in {"nan", "none", "-", "—", "n/a"}:
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
