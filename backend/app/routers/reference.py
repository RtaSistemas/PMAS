from __future__ import annotations

from collections import defaultdict
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Collaborator, TimesheetRecord

router = APIRouter(prefix="/api", tags=["reference"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/collaborators", summary="Listar colaboradores")
def list_collaborators(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
):
    q = db.query(Collaborator.id, Collaborator.name).join(
        TimesheetRecord, TimesheetRecord.collaborator_id == Collaborator.id
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))

    rows = q.distinct().order_by(Collaborator.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@router.get("/peps", summary="Listar PEPs únicos")
def list_peps(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
):
    q = db.query(
        TimesheetRecord.pep_wbs,
        TimesheetRecord.pep_description,
        func.count().label("n"),
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))

    rows = (
        q.filter(TimesheetRecord.pep_wbs.isnot(None))
        .group_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description)
        .order_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description)
        .all()
    )

    grouped: dict[str, dict] = defaultdict(
        lambda: {"code": "", "descriptions": [], "total_records": 0}
    )
    for r in rows:
        code = r.pep_wbs
        grouped[code]["code"] = code
        grouped[code]["total_records"] += r.n
        if r.pep_description and r.pep_description not in grouped[code]["descriptions"]:
            grouped[code]["descriptions"].append(r.pep_description)

    return sorted(grouped.values(), key=lambda x: x["total_records"], reverse=True)
