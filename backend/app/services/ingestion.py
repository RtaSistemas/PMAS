from __future__ import annotations

import logging
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models import Collaborator, Cycle, RateCard, TimesheetRecord

log = logging.getLogger(__name__)

_COL_COLLABORATOR = "Colaborador"
_COL_DATE = "Data"
_COL_HOURS = "Horas totais (decimal)"
_COL_EXTRA = "Hora extra"
_COL_STANDBY = "Hora sobreaviso"
_COL_PEP_CODE = "Código PEP"
_COL_PEP_DESC = "PEP"
_COL_START_TIME = "Hora Inicial [H]"


class ClosedCycleError(Exception):
    def __init__(self, cycle_names: list[str]) -> None:
        self.cycle_names = cycle_names
        super().__init__(f"Ciclos fechados: {', '.join(cycle_names)}")


def ingest_file(
    file_bytes: bytes,
    filename: str,
    db: Session,
    user_role: str = "admin",
) -> dict:
    df = _load_dataframe(file_bytes, filename)

    # Pass 1: resolve collaborators and cycles
    collab_cache: dict[str, Collaborator] = {}
    cycle_cache: dict[date, Cycle] = {}
    quarantine_cycles_created = 0

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

        # Collect (collaborator_id, cycle_id) pairs touched by this upload
        affected_pairs: set[tuple[int, int]] = set()
        for _, row in df.iterrows():
            collab = collab_cache[str(row[_COL_COLLABORATOR]).strip()]
            cycle = cycle_cache[_parse_date(row[_COL_DATE])]
            affected_pairs.add((collab.id, cycle.id))

        # RBAC: non-admins may not modify closed cycles
        if user_role != "admin":
            checked: set[int] = set()
            closed_names: list[str] = []
            for _, cycle_id in affected_pairs:
                if cycle_id in checked:
                    continue
                checked.add(cycle_id)
                c = db.get(Cycle, cycle_id)
                if c and c.is_closed:
                    closed_names.append(c.name)
            if closed_names:
                raise ClosedCycleError(closed_names)

        # DELETE existing records for all affected (collaborator, cycle) pairs
        for collab_id, cycle_id in affected_pairs:
            db.query(TimesheetRecord).filter(
                TimesheetRecord.collaborator_id == collab_id,
                TimesheetRecord.cycle_id == cycle_id,
            ).delete(synchronize_session=False)

        # INSERT fresh records (intra-batch dedup only)
        seen_keys: set[tuple] = set()
        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            collab = collab_cache[str(row[_COL_COLLABORATOR]).strip()]
            record_date = _parse_date(row[_COL_DATE])
            cycle = cycle_cache[record_date]

            normal_h = extra_h = standby_h = 0.0
            total_h = float(row[_COL_HOURS])

            if _is_yes(row.get(_COL_EXTRA, "")):
                extra_h = total_h
                hour_type = "extra"
            elif _is_yes(row.get(_COL_STANDBY, "")):
                standby_h = total_h
                hour_type = "standby"
            else:
                normal_h = total_h
                hour_type = "normal"

            pep_code   = _str_or_none(row.get(_COL_PEP_CODE))
            pep_desc   = _str_or_none(row.get(_COL_PEP_DESC))
            start_time = _str_or_none(row.get(_COL_START_TIME))

            key = (collab.id, cycle.id, record_date, pep_code, pep_desc, hour_type, start_time)
            if key in seen_keys:
                skipped += 1
                continue

            seen_keys.add(key)
            db.add(TimesheetRecord(
                collaborator_id=collab.id,
                cycle_id=cycle.id,
                record_date=record_date,
                pep_wbs=pep_code,
                pep_description=pep_desc,
                normal_hours=normal_h,
                extra_hours=extra_h,
                standby_hours=standby_h,
                cost_per_hour=_lookup_rate(db, collab, record_date),
            ))
            inserted += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    log.info(
        "Ingestão concluída: %d inseridos, %d duplicatas ignoradas, %d ciclos de quarentena.",
        inserted, skipped, quarantine_cycles_created,
    )
    return {
        "records_inserted": inserted,
        "records_skipped": skipped,
        "quarantine_cycles_created": quarantine_cycles_created,
    }


def ingest_csv(file_bytes: bytes, db: Session) -> dict:
    return ingest_file(file_bytes, "file.csv", db)


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
        # Excel stores dates as days since 1899-12-30
        return date(1899, 12, 30) + timedelta(days=int(value))
    return pd.to_datetime(str(value), dayfirst=True).date()


def _is_yes(value) -> bool:
    return str(value).strip().lower() in {"sim", "yes", "s", "y", "true", "1"}


def _str_or_none(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in {"nan", "none", ""} else s


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
