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
    GlobalConfig,
    Project,
    RateCard,
    TimesheetRecord,
    UserProjectAccess,
)

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
_HARD_CAP_HOURS = 24.0


class ClosedCycleError(Exception):
    def __init__(self, cycle_names: list[str]) -> None:
        self.cycle_names = cycle_names
        super().__init__(f"Ciclos fechados: {', '.join(cycle_names)}")


class LockedProjectError(Exception):
    def __init__(self, project_names: list[str]) -> None:
        self.project_names = project_names
        super().__init__(f"Projetos encerrados/suspensos: {', '.join(project_names)}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ingest_file(
    file_bytes: bytes,
    filename: str,
    db: Session,
    user_role: str = "admin",
    user_id: int | None = None,
) -> dict:
    df = _load_dataframe(file_bytes, filename)
    ingest_warnings: list[str] = []

    # Layer 1: Authorization filter (read-only, outside transaction)
    # Determine which named PEP codes are present in the file.
    pep_codes_raw: set[str] = set()
    if _COL_PEP_CODE in df.columns:
        pep_codes_raw = {_str_or_none(v) for v in df[_COL_PEP_CODE]} - {None}

    # Auth filter only applies when there is a concrete user_id.
    # user_id=None means system-level or test call — behaves like admin for filtering.
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

    # High-volume warning (checked before any DB writes)
    if len(df) > _MAX_ROWS_WARNING:
        ingest_warnings.append(
            f"Arquivo com volume elevado: {len(df)} linhas. "
            f"Verifique se o período exportado está correto."
        )

    # Filter rows with invalid collaborator names (e.g. Excel merged cells → "nan")
    _collab_invalid = df[_COL_COLLABORATOR].apply(
        lambda v: len(str(v).strip()) < 2 or str(v).strip().lower() in _INVALID_COLLAB_NAMES
    ).astype(bool)
    n_bad_collabs = int(_collab_invalid.sum())
    if n_bad_collabs:
        ingest_warnings.append(
            f"{n_bad_collabs} linha(s) ignorada(s) por nome de colaborador inválido."
        )
        df = df[~_collab_invalid].copy()

    # Pass 1: resolve collaborators and cycles
    collab_cache: dict[str, Collaborator] = {}
    cycle_cache: dict[date, Cycle] = {}
    quarantine_cycles_created = 0
    pep_codes_in_file: set[str] = set()

    try:
        for _, row in df.iterrows():
            name = str(row[_COL_COLLABORATOR]).strip()
            if name not in collab_cache:
                collab_cache[name] = _get_or_create_collaborator(db, name)

            record_date: date = _parse_date(row[_COL_DATE])
            if record_date not in cycle_cache:
                cycle, created = _resolve_cycle(db, record_date)
                cycle_cache[record_date] = cycle
                if created:
                    quarantine_cycles_created += 1

        # Layer 2: RBAC — non-admins cannot write to closed cycles
        if user_role != "admin":
            closed_names: list[str] = []
            seen_cycle_ids: set[int] = set()
            for cycle in cycle_cache.values():
                if cycle.id not in seen_cycle_ids and cycle.is_closed:
                    closed_names.append(cycle.name)
                seen_cycle_ids.add(cycle.id)
            if closed_names:
                raise ClosedCycleError(closed_names)

        # Collect PEP codes that will actually be processed (post-auth-filter)
        pep_codes_in_file = {
            _str_or_none(row.get(_COL_PEP_CODE))
            for _, row in df.iterrows()
        } - {None}

        # Block ingestion into encerrado/suspenso projects
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

        # Layer 3: Surgical DELETE by (pep_wbs, cycle_id)
        #
        # Unit of replacement = (PEP, cycle) block, not (collaborator, cycle).
        # Guarantees:
        #   - PM-A uploading PEP-A never touches PEP-B rows in the same cycle.
        #   - Collaborators absent from the new CSV have their old rows removed.
        #   - NULL-pep rows fall back to (collaborator, cycle) to avoid clobbering
        #     un-coded entries from other users.

        pep_cycle_scope: set[tuple[str | None, int]] = set()
        for _, row in df.iterrows():
            pep = _str_or_none(row.get(_COL_PEP_CODE))
            cycle = cycle_cache[_parse_date(row[_COL_DATE])]
            pep_cycle_scope.add((pep, cycle.id))

        # Named PEPs: delete the entire (pep_wbs, cycle) block
        for pep_code, cycle_id in pep_cycle_scope:
            if pep_code is not None:
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.pep_wbs == pep_code,
                    TimesheetRecord.cycle_id == cycle_id,
                ).delete(synchronize_session=False)

        # NULL-pep rows: scoped to (collaborator, cycle, pep_wbs IS NULL)
        null_by_cycle: dict[int, set[int]] = {}
        for _, row in df.iterrows():
            if _str_or_none(row.get(_COL_PEP_CODE)) is None:
                collab_id = collab_cache[str(row[_COL_COLLABORATOR]).strip()].id
                cycle_id = cycle_cache[_parse_date(row[_COL_DATE])].id
                null_by_cycle.setdefault(cycle_id, set()).add(collab_id)

        for cycle_id, collab_ids in null_by_cycle.items():
            for collab_id in collab_ids:
                db.query(TimesheetRecord).filter(
                    TimesheetRecord.collaborator_id == collab_id,
                    TimesheetRecord.cycle_id == cycle_id,
                    TimesheetRecord.pep_wbs.is_(None),
                ).delete(synchronize_session=False)

        # INSERT fresh records (intra-batch dedup)
        seen_keys: set[tuple] = set()
        inserted = 0
        skipped = 0
        warned_zero_rate: set[str] = set()

        for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
            collab = collab_cache[str(row[_COL_COLLABORATOR]).strip()]
            record_date = _parse_date(row[_COL_DATE])
            cycle = cycle_cache[record_date]

            normal_h = extra_h = standby_h = 0.0
            total_h = _safe_hours(row[_COL_HOURS], row_idx, _COL_HOURS, ingest_warnings)

            if total_h == 0.0:
                skipped += 1
                continue

            is_extra   = _is_yes(row.get(_COL_EXTRA, ""))
            is_standby = _is_yes(row.get(_COL_STANDBY, ""))

            if is_extra and is_standby:
                ingest_warnings.append(
                    f"Linha {row_idx}: colaborador '{collab.name}' em {record_date} "
                    f"marcado como Extra E Sobreaviso simultaneamente → classificado como Extra."
                )

            if is_extra:
                extra_h   = total_h
                hour_type = "extra"
            elif is_standby:
                standby_h = total_h
                hour_type = "standby"
            else:
                normal_h  = total_h
                hour_type = "normal"

            pep_code   = _str_or_none(row.get(_COL_PEP_CODE))
            pep_desc   = _str_or_none(row.get(_COL_PEP_DESC))
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

        db.commit()
    except Exception:
        db.rollback()
        raise

    cfg = db.get(GlobalConfig, 1)
    max_daily_hours = cfg.anomaly_max_daily_hours if cfg else 24.0
    anomaly_warnings = _detect_anomalies(df, pep_codes_in_file, db, max_daily_hours)
    ingest_warnings.extend(anomaly_warnings)

    log.info(
        "Ingestão concluída: %d inseridos, %d duplicatas ignoradas, "
        "%d ciclos de quarentena, %d alertas.",
        inserted, skipped, quarantine_cycles_created, len(ingest_warnings),
    )
    return {
        "records_inserted": inserted,
        "records_skipped": skipped,
        "quarantine_cycles_created": quarantine_cycles_created,
        "warnings": ingest_warnings,
        "anomaly_warnings": anomaly_warnings,
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
    """Return the subset of pep_codes the calling user may write.

    Admin  -> unrestricted (all codes).
    Others -> PEPs where they are manager_id (auto) OR have an ACL grant (manual).
    """
    if user_role == "admin" or not pep_codes:
        return set(pep_codes)
    if user_id is None:
        return set()

    # Auto-access: user is the registered project manager
    managed: set[str] = {
        p.pep_wbs
        for p in db.query(Project)
        .filter(Project.pep_wbs.in_(pep_codes), Project.manager_id == user_id)
        .all()
    }

    # Delegated access: explicit ACL entry granted by an admin
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

def _detect_anomalies(df: pd.DataFrame, pep_codes_in_file: set[str], db: Session, max_daily_hours: float = 24.0) -> list[str]:
    warnings: list[str] = []

    dates_parsed = pd.to_datetime(df[_COL_DATE], errors="coerce", dayfirst=True)
    weekend_mask = dates_parsed.dt.weekday.isin([5, 6])
    if weekend_mask.any():
        weekend_collabs = df.loc[weekend_mask, _COL_COLLABORATOR].unique().tolist()
        warnings.append(
            f"Registros em fim de semana detectados para: {', '.join(str(c) for c in weekend_collabs[:10])}"
            + (" e outros." if len(weekend_collabs) > 10 else ".")
        )

    df_work = df.copy()
    df_work["_date_key"] = dates_parsed.dt.date
    df_work["_hours"] = pd.to_numeric(df[_COL_HOURS], errors="coerce").fillna(0)
    daily_totals = df_work.groupby([_COL_COLLABORATOR, "_date_key"])["_hours"].sum()
    over_limit = daily_totals[daily_totals > max_daily_hours]
    if not over_limit.empty:
        cases = [f"{collab} em {d}" for (collab, d) in over_limit.index[:10]]
        warnings.append(
            f"Horas > {max_daily_hours:.0f}h/dia detectadas: {'; '.join(cases)}"
            + (" e outros." if len(over_limit) > 10 else ".")
        )

    today = date.today()
    future_mask = dates_parsed.dt.date > today
    if future_mask.any():
        future_collabs = df.loc[future_mask, _COL_COLLABORATOR].unique().tolist()
        future_dates   = dates_parsed[future_mask].dt.date.unique().tolist()
        warnings.append(
            f"Datas futuras detectadas (possível erro de digitação): "
            f"{', '.join(str(d) for d in future_dates[:5])} "
            f"— colaboradores: {', '.join(str(c) for c in future_collabs[:5])}"
            + (" e outros." if len(future_collabs) > 5 else ".")
        )

    if pep_codes_in_file:
        registered = {
            p.pep_wbs
            for p in db.query(Project).filter(Project.pep_wbs.in_(pep_codes_in_file)).all()
        }
        unregistered = sorted(pep_codes_in_file - registered)
        if unregistered:
            warnings.append(
                f"Códigos PEP sem cadastro em Projetos: {', '.join(unregistered[:20])}"
                + (" e outros." if len(unregistered) > 20 else ".")
            )

        suspicious_peps = [p for p in pep_codes_in_file if not _PEP_PATTERN.match(p)]
        if suspicious_peps:
            warnings.append(
                f"Códigos PEP com formato suspeito (verifique mapeamento de colunas): "
                f"{', '.join(sorted(suspicious_peps)[:10])}"
                + (" e outros." if len(suspicious_peps) > 10 else ".")
            )

    return warnings


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
    return df


def _get_or_create_collaborator(db: Session, name: str) -> Collaborator:
    collab = db.query(Collaborator).filter(Collaborator.name == name).first()
    if collab is None:
        collab = Collaborator(name=name)
        db.add(collab)
        db.flush()
    return collab


def _resolve_cycle(db: Session, record_date: date) -> tuple[Cycle, bool]:
    cycle = (
        db.query(Cycle)
        .filter(
            Cycle.start_date <= record_date,
            Cycle.end_date >= record_date,
            Cycle.is_quarantine == False,  # noqa: E712
        )
        .first()
    )
    if cycle is not None:
        return cycle, False

    cycle = (
        db.query(Cycle)
        .filter(Cycle.start_date <= record_date, Cycle.end_date >= record_date)
        .first()
    )
    if cycle is not None:
        return cycle, False

    start = record_date.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)

    name = f"Quarentena - {record_date.strftime('%b/%Y')}"
    quarantine = Cycle(name=name, start_date=start, end_date=end, is_quarantine=True)
    db.add(quarantine)
    db.flush()
    log.warning("Ciclo de quarentena criado: '%s'", name)
    return quarantine, True


def _parse_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return date(1899, 12, 30) + timedelta(days=int(value))
    return pd.to_datetime(str(value), dayfirst=True).date()


def _is_yes(value) -> bool:
    return str(value).strip().lower() in {"sim", "yes", "s", "y", "true", "1"}


def _str_or_none(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in {"nan", "none", ""} else s


def _safe_hours(value, row_index: int, col_name: str, warnings: list[str]) -> float:
    """Convert a cell value to a non-negative, finite float of hours.

    Returns 0.0 and appends a warning for: empty/None, non-numeric text,
    NaN, Inf, negative values, and values above _HARD_CAP_HOURS.
    Never propagates NaN, Inf, or negative values to the database.
    """
    if value is None:
        return 0.0

    raw = str(value).strip().replace(",", ".")

    if raw == "" or raw.lower() in {"nan", "none", "-", "—", "n/a"}:
        warnings.append(
            f"Linha {row_index}: valor ausente em '{col_name}' → tratado como 0h."
        )
        return 0.0

    try:
        v = float(raw)
    except (ValueError, TypeError):
        warnings.append(
            f"Linha {row_index}: valor não numérico em '{col_name}' "
            f"({value!r}) → tratado como 0h."
        )
        return 0.0

    if math.isnan(v) or math.isinf(v):
        warnings.append(
            f"Linha {row_index}: NaN/Inf em '{col_name}' → tratado como 0h."
        )
        return 0.0

    if v < 0:
        warnings.append(
            f"Linha {row_index}: horas negativas em '{col_name}' ({v}) → tratado como 0h."
        )
        return 0.0

    if v > _HARD_CAP_HOURS:
        warnings.append(
            f"Linha {row_index}: valor de horas absurdo em '{col_name}' "
            f"({v}h > {_HARD_CAP_HOURS}h) → tratado como 0h."
        )
        return 0.0

    return v


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
