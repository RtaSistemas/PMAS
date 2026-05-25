"""GET /api/v2/allocation — horas e custos por colaborador × PEP.

Granularidade (collaborator_id, pep_wbs) — não existe tabela de sumário
nessa granularidade, então sempre lê diretamente de TimesheetRecord.
ACL é aplicada via _allowed_peps.
"""
from __future__ import annotations

from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, TimesheetRecord
from backend.app.routers.v2.portfolio import _allowed_peps

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/allocation", summary="Alocação por colaborador × PEP — horas e custos")
def get_allocation(
    db: DbSession,
    current_user=Depends(get_current_user),
    pep_wbs: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    cycle_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    allowed = _allowed_peps(db, current_user)

    q = (
        db.query(
            TimesheetRecord.collaborator_id.label("collaborator_id"),
            Collaborator.name.label("collaborator"),
            TimesheetRecord.pep_wbs.label("pep_wbs"),
            TimesheetRecord.pep_description.label("pep_description"),
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(
                TimesheetRecord.normal_cost
                + TimesheetRecord.extra_cost
                + TimesheetRecord.standby_cost
            ).label("total_cost"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(TimesheetRecord.pep_wbs.isnot(None))
    )

    if allowed is not None:
        q = q.filter(TimesheetRecord.pep_wbs.in_(allowed))
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = (
        q.group_by(
            TimesheetRecord.collaborator_id,
            Collaborator.name,
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
        )
        .order_by(Collaborator.name, TimesheetRecord.pep_wbs)
        .all()
    )

    return [
        {
            "collaborator_id":  r.collaborator_id,
            "collaborator":     r.collaborator,
            "pep_wbs":          r.pep_wbs,
            "pep_description":  r.pep_description,
            "normal_hours":     round(r.normal_hours  or 0.0, 2),
            "extra_hours":      round(r.extra_hours   or 0.0, 2),
            "standby_hours":    round(r.standby_hours or 0.0, 2),
            "total_hours":      round(r.total_hours   or 0.0, 2),
            "total_cost":       round(r.total_cost    or 0.0, 2),
        }
        for r in rows
    ]
