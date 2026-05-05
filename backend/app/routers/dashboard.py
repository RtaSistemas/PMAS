from __future__ import annotations

from collections import defaultdict
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, GlobalConfig, Project, TimesheetRecord
from backend.app.schemas import CollaboratorTimelineItem, DashboardOut, PepRadarItem

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


def _compute_budget_vs_actual(
    db: Session,
    pep_codes: List[str],
    cycle_id: Optional[int] = None,
    collaborator_ids: Optional[List[int]] = None,
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
) -> list:
    if pep_codes:
        projects = (
            db.query(Project)
            .filter(Project.pep_wbs.in_(pep_codes), Project.budget_hours.isnot(None))
            .all()
        )
    else:
        projects = db.query(Project).filter(Project.budget_hours.isnot(None)).all()

    if not projects:
        return []

    budget_peps = [p.pep_wbs for p in projects]
    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
        )
        .filter(TimesheetRecord.pep_wbs.in_(budget_peps))
    )
    if cycle_id is not None:
        q = q.filter(TimesheetRecord.cycle_id == cycle_id)
    if collaborator_ids:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_ids))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    actual_by_pep = {
        r.pep_wbs: r.total_hours or 0.0
        for r in q.group_by(TimesheetRecord.pep_wbs).all()
    }

    return sorted(
        [
            {
                "pep_wbs": p.pep_wbs,
                "name": p.name,
                "budget_hours": p.budget_hours,
                "actual_hours": actual_by_pep.get(p.pep_wbs, 0.0),
            }
            for p in projects
        ],
        key=lambda x: x["budget_hours"],
        reverse=True,
    )


def _aggregate_hours(rows) -> tuple[dict, list]:
    """Returns (per_collaborator_totals, breakdown_list)."""
    per_collab: dict[str, dict] = defaultdict(
        lambda: {"normal_hours": 0.0, "extra_hours": 0.0, "standby_hours": 0.0}
    )
    breakdown = []
    for r in rows:
        per_collab[r.collaborator]["normal_hours"] += r.normal_hours or 0.0
        per_collab[r.collaborator]["extra_hours"] += r.extra_hours or 0.0
        per_collab[r.collaborator]["standby_hours"] += r.standby_hours or 0.0
        breakdown.append(
            {
                "collaborator": r.collaborator,
                "pep_code": r.pep_wbs,
                "pep_description": r.pep_description,
                "normal_hours": r.normal_hours or 0.0,
                "extra_hours": r.extra_hours or 0.0,
                "standby_hours": r.standby_hours or 0.0,
            }
        )
    chart_data = [
        {"collaborator": name, **hours}
        for name, hours in sorted(
            per_collab.items(),
            key=lambda x: -(
                x[1]["normal_hours"] + x[1]["extra_hours"] + x[1]["standby_hours"]
            ),
        )
    ]
    return chart_data, breakdown


def _base_query(db: Session):
    return db.query(
        Collaborator.id.label("collaborator_id"),
        Collaborator.name.label("collaborator"),
        TimesheetRecord.pep_wbs,
        TimesheetRecord.pep_description,
        func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
        func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
        func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
    ).join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)


@router.get("/pep-radar", summary="Horas e custo por PEP (descrição) para radar chart", response_model=list[PepRadarItem])
def get_pep_radar(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 1.0

    q = (
        db.query(
            TimesheetRecord.pep_description,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(
                TimesheetRecord.cost_per_hour * (
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours * em
                    + TimesheetRecord.standby_hours * sm
                )
            ).label("actual_cost"),
        )
        .filter(TimesheetRecord.pep_description.isnot(None))
    )

    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = (
        q.group_by(TimesheetRecord.pep_description)
        .order_by(
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).desc()
        )
        .limit(12)
        .all()
    )
    return [
        {
            "pep_description": r.pep_description,
            "total_hours": round(r.total_hours or 0.0, 2),
            "actual_cost": round(r.actual_cost or 0.0, 2),
        }
        for r in rows
    ]


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
        .filter(
            Collaborator.name == collaborator_name,
            Cycle.is_quarantine == False,  # noqa: E712
        )
    )
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)
    rows = (
        q.group_by(Cycle.id)
        .order_by(Cycle.start_date)
        .all()
    )
    return [
        {
            "cycle_name": r.cycle_name,
            "normal_hours": round(r.normal_hours or 0.0, 2),
            "extra_hours": round(r.extra_hours or 0.0, 2),
            "standby_hours": round(r.standby_hours or 0.0, 2),
        }
        for r in rows
    ]


@router.get("", summary="Dashboard sem filtro de ciclo — toda a base", response_model=DashboardOut)
def get_dashboard_all(
    db: DbSession,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    q = _base_query(db)
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(TimesheetRecord.collaborator_id).order_by(Collaborator.name).all()
    chart_data, _ = _aggregate_hours(rows)

    return {
        "cycle": {
            "id": None,
            "name": "Toda a base",
            "start_date": None,
            "end_date": None,
            "is_quarantine": False,
        },
        "filters": {
            "pep_codes": pep_code,
            "pep_descriptions": pep_description,
            "collaborator_ids": collaborator_id,
        },
        "data": chart_data,
        "breakdown": [],
        "budget_vs_actual": _compute_budget_vs_actual(db, pep_code, None, collaborator_id, date_from, date_to),
    }


@router.get("/{cycle_id}", summary="Dashboard de horas por ciclo", response_model=DashboardOut)
def get_dashboard(
    cycle_id: int,
    db: DbSession,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")

    q = _base_query(db).filter(TimesheetRecord.cycle_id == cycle_id)
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    if not pep_description:
        rows = (
            q.group_by(TimesheetRecord.collaborator_id, TimesheetRecord.pep_description)
            .order_by(Collaborator.name, TimesheetRecord.pep_description)
            .all()
        )
    else:
        rows = (
            q.group_by(TimesheetRecord.collaborator_id)
            .order_by(Collaborator.name)
            .all()
        )

    chart_data, breakdown = _aggregate_hours(rows)

    return {
        "cycle": {
            "id": cycle.id,
            "name": cycle.name,
            "start_date": cycle.start_date,
            "end_date": cycle.end_date,
            "is_quarantine": cycle.is_quarantine,
        },
        "filters": {
            "pep_codes": pep_code,
            "pep_descriptions": pep_description,
            "collaborator_ids": collaborator_id,
        },
        "data": chart_data,
        "breakdown": breakdown,
        "budget_vs_actual": _compute_budget_vs_actual(db, pep_code, cycle_id, collaborator_id, date_from, date_to),
    }
