"""GET /api/v2/effort — replaces /api/dashboard and /api/dashboard/{cycle_id}.

Reads from `collaborator_cycle_summary` (pre-computed) for fast aggregation.
Falls back to raw TimesheetRecord if summary tables are empty.
ACL is enforced via UserProjectAccess.
"""
from __future__ import annotations

from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Collaborator, CollaboratorCycleSummary, Cycle,
    TimesheetRecord, UserProjectAccess, Project,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/effort", summary="Esforço da equipe por colaborador — render-ready")
def get_effort(
    db: DbSession,
    current_user=Depends(get_current_user),
    cycle_id: List[int] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    # ACL: restrict collaborators to those who worked on allowed PEPs
    allowed_collab_ids: list[int] | None = None
    if current_user.role != "admin":
        access = db.query(UserProjectAccess).filter_by(user_id=current_user.id).all()
        if access:
            proj_ids = [a.project_id for a in access]
            allowed_peps = [p.pep_wbs for p in db.query(Project).filter(Project.id.in_(proj_ids)).all()]
            collab_ids_in_peps = [
                r[0]
                for r in db.query(TimesheetRecord.collaborator_id)
                .filter(TimesheetRecord.pep_wbs.in_(allowed_peps))
                .distinct()
                .all()
            ]
            allowed_collab_ids = collab_ids_in_peps

    has_summaries = db.query(CollaboratorCycleSummary).first() is not None

    if has_summaries and not pep_wbs:
        return _effort_from_summary(db, cycle_id, collaborator_id, date_from, date_to,
                                    allowed_collab_ids)

    return _effort_fallback(db, cycle_id, collaborator_id, pep_wbs, date_from, date_to,
                            allowed_collab_ids)


def _effort_from_summary(db, cycle_ids, collab_ids, date_from, date_to, allowed_collab_ids):
    q = (
        db.query(CollaboratorCycleSummary)
        .join(Cycle, CollaboratorCycleSummary.cycle_id == Cycle.id)
        .join(Collaborator, CollaboratorCycleSummary.collaborator_id == Collaborator.id)
    )
    if cycle_ids:
        q = q.filter(CollaboratorCycleSummary.cycle_id.in_(cycle_ids))
    if date_from:
        q = q.filter(Cycle.start_date >= date_from)
    if date_to:
        q = q.filter(Cycle.end_date <= date_to)
    if collab_ids:
        q = q.filter(CollaboratorCycleSummary.collaborator_id.in_(collab_ids))
    if allowed_collab_ids is not None:
        q = q.filter(CollaboratorCycleSummary.collaborator_id.in_(allowed_collab_ids))

    rows = q.all()

    by_collab: dict[int, dict] = {}
    for r in rows:
        entry = by_collab.setdefault(r.collaborator_id, {
            "collaborator_id": r.collaborator_id,
            "collaborator": r.collaborator.name,
            "normal_hours": 0.0,
            "extra_hours": 0.0,
            "standby_hours": 0.0,
            "total_hours": 0.0,
            "total_cost": 0.0,
        })
        entry["normal_hours"]  += r.normal_hours  or 0.0
        entry["extra_hours"]   += r.extra_hours   or 0.0
        entry["standby_hours"] += r.standby_hours or 0.0
        entry["total_hours"]   += r.total_hours   or 0.0
        entry["total_cost"]    += r.total_cost    or 0.0

    result = sorted(by_collab.values(), key=lambda x: x["total_hours"], reverse=True)
    for r in result:
        r["normal_hours"]  = round(r["normal_hours"],  2)
        r["extra_hours"]   = round(r["extra_hours"],   2)
        r["standby_hours"] = round(r["standby_hours"], 2)
        r["total_hours"]   = round(r["total_hours"],   2)
        r["total_cost"]    = round(r["total_cost"],    2)
    return result


def _effort_fallback(db, cycle_ids, collab_ids, pep_wbs_filter, date_from, date_to,
                     allowed_collab_ids):
    q = (
        db.query(
            Collaborator.id.label("collaborator_id"),
            Collaborator.name.label("collaborator"),
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
    )
    if cycle_ids:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_ids))
    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)
    if collab_ids:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collab_ids))
    if pep_wbs_filter:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs_filter))
    if allowed_collab_ids is not None:
        q = q.filter(TimesheetRecord.collaborator_id.in_(allowed_collab_ids))

    rows = q.group_by(Collaborator.id).order_by(func.sum(
        TimesheetRecord.normal_hours + TimesheetRecord.extra_hours + TimesheetRecord.standby_hours
    ).desc()).all()

    return [
        {
            "collaborator_id": r.collaborator_id,
            "collaborator": r.collaborator,
            "normal_hours":  round(r.normal_hours  or 0.0, 2),
            "extra_hours":   round(r.extra_hours   or 0.0, 2),
            "standby_hours": round(r.standby_hours or 0.0, 2),
            "total_hours":   round(r.total_hours   or 0.0, 2),
            "total_cost":    0.0,
        }
        for r in rows
    ]
