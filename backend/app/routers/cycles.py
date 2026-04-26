from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import Cycle, TimesheetRecord
from backend.app.schemas import CycleIn, CycleOut

router = APIRouter(prefix="/api/cycles", tags=["cycles"], dependencies=[Depends(get_current_user)])


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
def create_cycle(body: CycleIn, db: DbSession):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    cycle = Cycle(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        is_quarantine=False,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return _cycle_to_dict(cycle, 0)


@router.put("/{cycle_id}", summary="Atualizar ciclo", response_model=CycleOut)
def update_cycle(cycle_id: int, body: CycleIn, db: DbSession):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    cycle.name = body.name
    cycle.start_date = body.start_date
    cycle.end_date = body.end_date
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
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return _cycle_to_dict(cycle, counts.get(cycle.id, 0))


@router.delete("/{cycle_id}", summary="Excluir ciclo", status_code=204)
def delete_cycle(cycle_id: int, db: DbSession):
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
    db.delete(cycle)
    db.commit()
