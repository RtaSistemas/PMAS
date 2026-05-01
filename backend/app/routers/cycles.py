from __future__ import annotations

import io
from datetime import date as DateType

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import Cycle, TimesheetRecord
from backend.app.schemas import CycleIn, CycleOut, ImportResultOut

router = APIRouter(prefix="/api/cycles", tags=["cycles"], dependencies=[Depends(get_current_user)])


def _check_overlap(db: Session, start, end, exclude_id: int | None = None) -> None:
    q = db.query(Cycle).filter(
        Cycle.is_quarantine == False,  # noqa: E712
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
        "is_quarantine": c.is_quarantine,
        "is_closed": c.is_closed,
        "record_count": record_count,
    }


@router.get("", summary="Listar ciclos", response_model=list[CycleOut])
def list_cycles(db: DbSession):
    cycles = db.query(Cycle).order_by(Cycle.start_date).all()
    counts = _cycle_record_counts(db)
    return [_cycle_to_dict(c, counts.get(c.id, 0)) for c in cycles]


@router.post("", summary="Criar ciclo", status_code=201, response_model=CycleOut)
def create_cycle(body: CycleIn, db: DbSession, current_user: CurrentUser):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    _check_overlap(db, body.start_date, body.end_date)
    cycle = Cycle(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        is_quarantine=False,
    )
    db.add(cycle)
    db.flush()
    log_audit(db, current_user, "create", "cycle", cycle.id, {"name": cycle.name})
    db.commit()
    db.refresh(cycle)
    return _cycle_to_dict(cycle, 0)


@router.put("/{cycle_id}", summary="Atualizar ciclo", response_model=CycleOut)
def update_cycle(cycle_id: int, body: CycleIn, db: DbSession, current_user: CurrentUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    _check_overlap(db, body.start_date, body.end_date, exclude_id=cycle_id)
    cycle.name = body.name
    cycle.start_date = body.start_date
    cycle.end_date = body.end_date
    log_audit(db, current_user, "update", "cycle", cycle_id, body.model_dump())
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


@router.patch("/{cycle_id}/toggle-status", summary="Bloquear/desbloquear ciclo", response_model=CycleOut)
def toggle_cycle_status(cycle_id: int, db: DbSession, _admin: AdminUser):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    cycle.is_closed = not cycle.is_closed
    log_audit(db, _admin, "toggle_status", "cycle", cycle_id, {"is_closed": cycle.is_closed})
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


@router.post("/import", summary="Importar ciclos via CSV", response_model=ImportResultOut)
def import_cycles(file: UploadFile, db: DbSession, current_user: CurrentUser):
    try:
        raw = file.file.read()
        df = pd.read_csv(io.BytesIO(raw))
        df.columns = [c.strip() for c in df.columns]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {e}")
    required = {"name", "start_date", "end_date"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {missing}")
    created, errors = 0, []
    for i, row in df.iterrows():
        try:
            name = str(row["name"]).strip()
            if not name or name.lower() in {"nan", "none"}:
                errors.append(f"Linha {i + 2}: nome vazio")
                continue
            start: DateType = pd.to_datetime(str(row["start_date"])).date()
            end: DateType = pd.to_datetime(str(row["end_date"])).date()
            if end < start:
                errors.append(f"Linha {i + 2}: end_date antes de start_date para '{name}'")
                continue
            if db.query(Cycle).filter(Cycle.name == name).first():
                continue
            overlap = db.query(Cycle).filter(
                Cycle.is_quarantine == False,  # noqa: E712
                Cycle.start_date <= end,
                Cycle.end_date >= start,
            ).first()
            if overlap:
                errors.append(f"Linha {i + 2}: sobreposição com ciclo '{overlap.name}'")
                continue
            db.add(Cycle(name=name, start_date=start, end_date=end, is_quarantine=False))
            created += 1
        except Exception as exc:
            db.rollback()
            created = 0
            errors.append(f"Linha {i + 2}: {exc}")
    try:
        if created:
            log_audit(db, current_user, "import", "cycle", detail={"created": created, "errors": len(errors)})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=f"Erro ao persistir ciclos: {exc}")
    return {"created": created, "updated": 0, "errors": errors}


@router.delete("/{cycle_id}", summary="Excluir ciclo", status_code=204)
def delete_cycle(cycle_id: int, db: DbSession, current_user: CurrentUser):
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
    log_audit(db, current_user, "delete", "cycle", cycle_id, {"name": cycle.name})
    db.delete(cycle)
    db.commit()
