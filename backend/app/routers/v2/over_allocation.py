"""GET /api/v2/over-allocation — detects collaborators whose total daily hours
exceed a configurable threshold.

Auth: logged-in user required.  Admin sees all collaborators; regular users
are filtered to their ACL-allowed PEPs (via _allowed_peps from portfolio.py).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Collaborator, Cycle, GlobalConfig, TimesheetRecord,
)
from backend.app.routers.v2.portfolio import _allowed_peps

router = APIRouter(prefix="/api/v2", tags=["v2"])

_DEFAULT_THRESHOLD = 24.0


class OverAllocationItem(BaseModel):
    collaborator: str
    date: DateType
    total_hours: float
    threshold: float
    pep_list: list[str]


@router.get(
    "/over-allocation",
    summary="Detecção de sobre-alocação diária por colaborador",
    response_model=list[OverAllocationItem],
)
def get_over_allocation(
    db: DbSession,
    current_user=Depends(get_current_user),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
    threshold: Optional[float] = Query(default=None, gt=0),
):
    # Resolve effective threshold: param > GlobalConfig > hard default
    cfg = db.get(GlobalConfig, 1)
    if threshold is not None:
        eff_threshold = threshold
    elif cfg is not None and cfg.anomaly_max_daily_hours is not None:
        eff_threshold = cfg.anomaly_max_daily_hours
    else:
        eff_threshold = _DEFAULT_THRESHOLD

    # ACL: restrict to allowed PEPs for non-admin users
    allowed = _allowed_peps(db, current_user)

    # Step 1: query all (collaborator, date, pep_wbs, sum_hours) rows
    q = (
        db.query(
            Collaborator.name.label("collaborator"),
            TimesheetRecord.record_date,
            TimesheetRecord.pep_wbs,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("day_pep_hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Cycle.is_active.is_(True))  # exclude quarantine/inactive cycles
    )

    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)
    if allowed is not None:
        q = q.filter(TimesheetRecord.pep_wbs.in_(allowed))

    q = q.group_by(
        Collaborator.name,
        TimesheetRecord.record_date,
        TimesheetRecord.pep_wbs,
    )

    rows = q.all()

    # Step 2: aggregate in Python by (collaborator, date)
    day_totals: dict = defaultdict(lambda: {"total": 0.0, "peps": set()})
    for r in rows:
        key = (r.collaborator, r.record_date)
        day_totals[key]["total"] += r.day_pep_hours or 0.0
        if r.pep_wbs:
            day_totals[key]["peps"].add(r.pep_wbs)

    # Step 3: filter by threshold and build response, sorted by date desc then total_hours desc
    violations = []
    for (collab, dt), info in sorted(
        day_totals.items(),
        key=lambda x: (-x[1]["total"], x[0][1] if x[0][1] else DateType.min, x[0][0]),
    ):
        if info["total"] > eff_threshold:
            violations.append(
                OverAllocationItem(
                    collaborator=collab,
                    date=dt,
                    total_hours=round(info["total"], 2),
                    threshold=eff_threshold,
                    pep_list=sorted(info["peps"]),
                )
            )

    # Sort by date desc, then total_hours desc
    violations.sort(key=lambda v: (v.date, v.total_hours), reverse=True)

    return violations
