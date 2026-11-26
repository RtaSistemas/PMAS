from __future__ import annotations

import io
import re
from datetime import date as DateType

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.limiter import limiter
from backend.app.models import Cycle, ProjectCyclePlan, TimesheetRecord
from backend.app.schemas import CycleIn, CycleOut, ImportResultOut
from backend.app.utils import csv_unsafe

router = APIRouter(prefix="/api/cycles", tags=["cycles"], dependencies=[Depends(get_current_user)])


def _check_overlap(db: Session, start, end, exclude_id: int | None = None) -> None:
    q = db.query(Cycle).filter(
        Cycle.start_date <= end,
        Cycle.end_date >= start,
    )
    if exclude_id is not None:
        q = q.filter(Cycle.id != exclude_id)
    conflict = q.first()
    if conflict:
        raise HTTPException(
            status_code=422,
            detail=f"Datas sobrepostas com o ciclo '{conflict.name}' ({conflict.start_date} — {conflict.end_date}).",
        )


def _assert_unique_name(db: Session, name: str, exclude_id: int | None = None) -> None:
    """Cycle names are unique ignoring case and surrounding spaces."""
    q = db.query(Cycle).filter(func.lower(func.trim(Cycle.name)) == name.strip().lower())
    if exclude_id is not None:
        q = q.filter(Cycle.id != exclude_id)
    conflict = q.first()
    if conflict:
        raise HTTPException(status_code=409, detail=f"Já existe um ciclo com o nome '{conflict.name}'.")


def _parse_date(raw) -> DateType:
    """ISO first (4-digit year first); otherwise day-first (dd/mm/yyyy)."""
    s = str(raw).strip()
    if not s or s.lower() in {"nan", "none", "nat"}:
        raise ValueError("data vazia")
    try:
        if re.match(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", s):
            return pd.to_datetime(s.replace("/", "-").replace(".", "-")).date()
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:
        raise ValueError(f"data inválida ({s!r})")


def _cycle_record_counts(db: Session) -> dict[int, int]:
    rows = (
        db.query(TimesheetRecord.cycle_id, func.count(TimesheetRecord.id))
        .group_by(TimesheetRecord.cycle_id)
        .all()
    )
    return {cycle_id: cnt for cycle_id, cnt in rows}


def _cycle_to_dict(c: Cycle, record_count: int = 0) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "start_date": c.start_date,
        "end_date": c.end_date,
        "is_closed": c.is_closed,
        "is_active": c.is_active,
        "record_count": record_count,
    }


@router.get("", summary="Listar ciclos", response_model=list[CycleOut])
def list_cycles(db: DbSession, include_archived: bool = False):
    q = db.query(Cycle)
    if not include_archived:
        q = q.filter(Cycle.is_active == True)  # noqa: E712
    cycles = q.order_by(Cycle.start_date).all()
    counts = _cycle_record_counts(db)
    return [_cycle_to_dict(c, counts.get(c.id, 0)) for c in cycles]


@router.post("", summary="Criar ciclo", status_code=201, response_model=CycleOut)
@limiter.limit("30/minute")
def create_cycle(request: Request, body: CycleIn, db: DbSession, current_user: AdminUser):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    _check_overlap(db, body.start_date, body.end_date)
    _assert_unique_name(db, body.name)
    cycle = Cycle(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    db.add(cycle)
    db.flush()
    log_audit(db, current_user, "create", "cycle", cycle.id, {"name": cycle.name})
    db.commit()
    db.refresh(cycle)
    return _cycle_to_dict(cycle, 0)


@router.put("/{cycle_id}", summary="Atualizar ciclo", response_model=CycleOut)
@limiter.limit("30/minute")
def update_cycle(request: Request, cycle_id: int, body: CycleIn, db: DbSession, current_user: AdminUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    if cycle.is_closed:
        raise HTTPException(
            status_code=409,
            detail="Ciclo fechado não pode ser editado. Reabra o ciclo antes de alterá-lo.",
        )
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    _check_overlap(db, body.start_date, body.end_date, exclude_id=cycle_id)
    _assert_unique_name(db, body.name, exclude_id=cycle_id)
    if (body.start_date, body.end_date) != (cycle.start_date, cycle.end_date):
        outside = db.query(func.count(TimesheetRecord.id)).filter(
            TimesheetRecord.cycle_id == cycle_id,
            (TimesheetRecord.record_date < body.start_date) | (TimesheetRecord.record_date > body.end_date),
        ).scalar()
        if outside:
            raise HTTPException(
                status_code=409,
                detail=f"{outside} registro(s) do ciclo ficariam fora do novo período. "
                       "Ajuste as datas para cobrir todos os registros.",
            )
    cycle.name = body.name
    cycle.start_date = body.start_date
    cycle.end_date = body.end_date
    log_audit(db, current_user, "update", "cycle", cycle_id, body.model_dump())
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


@router.patch("/{cycle_id}/toggle-status", summary="Bloquear/desbloquear ciclo", response_model=CycleOut)
@limiter.limit("30/minute")
def toggle_cycle_status(request: Request, cycle_id: int, db: DbSession, _admin: AdminUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    cycle.is_closed = not cycle.is_closed
    log_audit(db, _admin, "toggle_status", "cycle", cycle_id, {"is_closed": cycle.is_closed})
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


@router.patch("/{cycle_id}/toggle-archive", summary="Arquivar/restaurar ciclo", response_model=CycleOut)
@limiter.limit("30/minute")
def toggle_cycle_archive(request: Request, cycle_id: int, db: DbSession, _admin: AdminUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    cycle.is_active = not cycle.is_active
    log_audit(db, _admin, "toggle_archive", "cycle", cycle_id, {"is_active": cycle.is_active})
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/import", summary="Importar ciclos via CSV", response_model=ImportResultOut)
@limiter.limit("30/minute")
def import_cycles(request: Request, file: UploadFile, db: DbSession, current_user: AdminUser):
    try:
        raw = file.file.read()
        if len(raw) > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo CSV excede o limite de 10 MB.")
        df = pd.read_csv(io.BytesIO(raw))
        df.columns = [c.strip() for c in df.columns]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {e}")
    required = {"name", "start_date", "end_date"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {missing}")
    created, errors = 0, []
    seen_names = {
        (c.name or "").strip().lower() for c in db.query(Cycle).all()
    }
    for i, row in df.iterrows():
        try:
            name = csv_unsafe(str(row["name"])).strip()
            if not name or name.lower() in {"nan", "none"}:
                errors.append(f"Linha {i + 2}: nome vazio")
                continue
            try:
                start: DateType = _parse_date(row["start_date"])
                end: DateType = _parse_date(row["end_date"])
            except ValueError as exc:
                errors.append(f"Linha {i + 2}: {exc}")
                continue
            if end < start:
                errors.append(f"Linha {i + 2}: end_date antes de start_date para '{name}'")
                continue
            if name.lower() in seen_names:
                continue
            overlap = db.query(Cycle).filter(
                Cycle.start_date <= end,
                Cycle.end_date >= start,
            ).first()
            if overlap:
                errors.append(f"Linha {i + 2}: sobreposição com ciclo '{overlap.name}'")
                continue
            db.add(Cycle(name=name, start_date=start, end_date=end))
            db.flush()  # make the row visible to the overlap check of later rows
            seen_names.add(name.lower())
            created += 1
        except Exception as exc:
            errors.append(f"Linha {i + 2}: {str(exc).splitlines()[0][:120]}")
    try:
        if created:
            log_audit(db, current_user, "import", "cycle", detail={"created": created, "errors": len(errors)})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Erro ao persistir ciclos: {exc}")
    message = f"{created} criado(s), {len(errors)} erro(s)."
    return {"created": created, "updated": 0, "errors": errors, "message": message}


@router.delete("/{cycle_id}", summary="Excluir ciclo", status_code=204)
@limiter.limit("30/minute")
def delete_cycle(request: Request, cycle_id: int, db: DbSession, current_user: AdminUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    count = db.query(func.count(TimesheetRecord.id)).filter(
        TimesheetRecord.cycle_id == cycle_id
    ).scalar()
    if count:
        raise HTTPException(
            status_code=409,
            detail=f"Ciclo possui {count} registro(s). Remova os registros antes de excluir o ciclo.",
        )
    plans = db.query(func.count(ProjectCyclePlan.id)).filter(
        ProjectCyclePlan.cycle_id == cycle_id
    ).scalar()
    if plans:
        raise HTTPException(
            status_code=409,
            detail=f"Ciclo possui {plans} plano(s) de baseline. Remova os planos antes de excluir o ciclo.",
        )
    log_audit(db, current_user, "delete", "cycle", cycle_id, {"name": cycle.name})
    db.delete(cycle)
    db.commit()
