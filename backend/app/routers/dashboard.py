from __future__ import annotations

import calendar
from datetime import date as DateType, date
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, QuarantineRecord, TimesheetRecord
from backend.app.schemas import CollaboratorTimelineItem

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get(
    "/collaborator-timeline",
    summary="Horas por colaborador distribuídas por ciclo",
    response_model=list[CollaboratorTimelineItem],
)
def get_collaborator_timeline(
    db: DbSession,
    collaborator_name: str,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    q = (
        db.query(
            Cycle.name.label("cycle_name"),
            Cycle.start_date.label("cycle_start"),
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Collaborator.name == collaborator_name)
    )
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)
    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()
    return [
        {
            "cycle_name":    r.cycle_name,
            "cycle_start":   str(r.cycle_start),
            "normal_hours":  round(r.normal_hours  or 0.0, 2),
            "extra_hours":   round(r.extra_hours   or 0.0, 2),
            "standby_hours": round(r.standby_hours or 0.0, 2),
        }
        for r in rows
    ]


@router.get("/collaborator-daily", summary="Horas diárias de um colaborador")
def get_collaborator_daily(
    collaborator_name: str,
    year: int,
    month: int,
    db: DbSession,
    _user=Depends(get_current_user),
) -> List[Dict]:
    date_from = date(year, month, 1)
    date_to   = date(year, month, calendar.monthrange(year, month)[1])

    rows = (
        db.query(
            TimesheetRecord.record_date,
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .filter(
            Collaborator.name == collaborator_name,
            TimesheetRecord.record_date >= date_from,
            TimesheetRecord.record_date <= date_to,
        )
        .group_by(TimesheetRecord.record_date)
        .all()
    )

    hours_by_date = {
        r.record_date: {
            "hours":   round(r.hours        or 0.0, 2),
            "normal":  round(r.normal_hours  or 0.0, 2),
            "extra":   round(r.extra_hours   or 0.0, 2),
            "standby": round(r.standby_hours or 0.0, 2),
        }
        for r in rows
    }

    qr_rows = (
        db.query(QuarantineRecord)
        .filter(QuarantineRecord.review_status == "pending")
        .all()
    )

    quarantine_dates: set = set()
    for qr in qr_rows:
        raw = qr.raw_data or {}
        if raw.get("Colaborador") != collaborator_name:
            continue
        raw_date = raw.get("Data")
        if raw_date is None:
            continue
        try:
            import pandas as _pd
            parsed = _pd.to_datetime(raw_date, dayfirst=True).date()
        except Exception:
            continue
        if date_from <= parsed <= date_to:
            quarantine_dates.add(parsed)

    _empty = {"hours": 0.0, "normal": 0.0, "extra": 0.0, "standby": 0.0}
    result = []
    for d_ in sorted(set(hours_by_date.keys()) | quarantine_dates):
        hdata = hours_by_date.get(d_, _empty)
        has_q = d_ in quarantine_dates
        if hdata["hours"] > 0 or has_q:
            result.append({
                "date":           str(d_),
                "hours":          hdata["hours"],
                "normal_hours":   hdata["normal"],
                "extra_hours":    hdata["extra"],
                "standby_hours":  hdata["standby"],
                "has_quarantine": has_q,
            })
    return result
