from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Cycle, Project, TimesheetRecord

router = APIRouter(prefix="/api", tags=["analytics"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/portfolio-health", summary="Horas consumidas por PEP com budget da tabela Project")
def get_portfolio_health(
    db: DbSession,
    cycle_id: Optional[int] = None,
    pep_wbs: List[str] = Query(default=[]),
):
    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("consumed_hours"),
        )
        .filter(TimesheetRecord.pep_wbs.isnot(None))
    )
    if cycle_id is not None:
        q = q.filter(TimesheetRecord.cycle_id == cycle_id)
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))

    rows = q.group_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description).all()

    # Aggregate by pep_wbs (a PEP may appear with multiple pep_descriptions)
    pep_map: dict[str, dict] = {}
    for r in rows:
        if r.pep_wbs not in pep_map:
            pep_map[r.pep_wbs] = {
                "pep_wbs": r.pep_wbs,
                "pep_description": r.pep_description,
                "consumed_hours": 0.0,
            }
        pep_map[r.pep_wbs]["consumed_hours"] += r.consumed_hours or 0.0

    if not pep_map:
        return []

    projects = {
        p.pep_wbs: p
        for p in db.query(Project)
        .filter(Project.pep_wbs.in_(list(pep_map.keys())))
        .all()
    }

    result = [
        {
            "pep_wbs": key,
            "pep_description": data["pep_description"],
            "name": projects[key].name if key in projects else None,
            "budget_hours": projects[key].budget_hours if key in projects else None,
            "consumed_hours": data["consumed_hours"],
            "is_registered": key in projects,
        }
        for key, data in pep_map.items()
    ]
    result.sort(key=lambda x: x["consumed_hours"], reverse=True)
    return result


@router.get("/trends", summary="Queima de horas por ciclo em ordem cronológica")
def get_trends(
    db: DbSession,
    pep_wbs: List[str] = Query(default=[]),
):
    q = (
        db.query(
            Cycle.name.label("cycle_name"),
            Cycle.start_date.label("cycle_start"),
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
        )
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Cycle.is_quarantine == False)  # noqa: E712
    )
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()

    return [
        {
            "cycle_name": r.cycle_name,
            "normal_hours": r.normal_hours or 0.0,
            "extra_hours": r.extra_hours or 0.0,
            "standby_hours": r.standby_hours or 0.0,
        }
        for r in rows
    ]
