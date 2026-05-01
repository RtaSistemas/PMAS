from __future__ import annotations

import math
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, GlobalConfig, Project, TimesheetRecord
from backend.app.schemas import AllocationItem, BurnHistoryPoint, ForecastOut, PortfolioHealthItem, TrendItem

router = APIRouter(prefix="/api", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/portfolio-health", summary="Horas consumidas por PEP com budget da tabela Project", response_model=list[PortfolioHealthItem])
def get_portfolio_health(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 1.0

    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("consumed_hours"),
            func.sum(
                TimesheetRecord.cost_per_hour
                * (
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours * em
                    + TimesheetRecord.standby_hours * sm
                )
            ).label("actual_cost"),
        )
        .filter(TimesheetRecord.pep_wbs.isnot(None))
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description).all()

    # Aggregate by pep_wbs (a PEP may appear with multiple pep_descriptions)
    pep_map: dict[str, dict] = {}
    for r in rows:
        if r.pep_wbs not in pep_map:
            pep_map[r.pep_wbs] = {
                "pep_wbs": r.pep_wbs,
                "pep_description": r.pep_description,
                "consumed_hours": 0.0,
                "actual_cost": 0.0,
            }
        pep_map[r.pep_wbs]["consumed_hours"] += r.consumed_hours or 0.0
        pep_map[r.pep_wbs]["actual_cost"]    += r.actual_cost    or 0.0

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
            "budget_cost": projects[key].budget_cost if key in projects else None,
            "consumed_hours": data["consumed_hours"],
            "actual_cost": data["actual_cost"],
            "is_registered": key in projects,
        }
        for key, data in pep_map.items()
    ]
    result.sort(key=lambda x: x["consumed_hours"], reverse=True)
    return result


@router.get("/trends", summary="Queima de horas por ciclo em ordem cronológica", response_model=list[TrendItem])
def get_trends(
    db: DbSession,
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 1.0

    q = (
        db.query(
            Cycle.name.label("cycle_name"),
            Cycle.start_date.label("cycle_start"),
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
            func.sum(
                TimesheetRecord.cost_per_hour
                * (
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours * em
                    + TimesheetRecord.standby_hours * sm
                )
            ).label("actual_cost"),
        )
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Cycle.is_quarantine == False)  # noqa: E712
    )
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()

    return [
        {
            "cycle_name": r.cycle_name,
            "normal_hours": r.normal_hours or 0.0,
            "extra_hours": r.extra_hours or 0.0,
            "standby_hours": r.standby_hours or 0.0,
            "actual_cost": r.actual_cost or 0.0,
        }
        for r in rows
    ]


@router.get("/allocation", summary="Matriz horas/custo por colaborador × PEP", response_model=list[AllocationItem])
def get_allocation(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 1.0

    q = (
        db.query(
            Collaborator.name.label("collaborator"),
            TimesheetRecord.pep_wbs,
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
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = (
        q.group_by(Collaborator.name, TimesheetRecord.pep_wbs, TimesheetRecord.pep_description)
        .order_by(Collaborator.name)
        .all()
    )
    return [
        {
            "collaborator": r.collaborator,
            "pep_wbs": r.pep_wbs,
            "pep_description": r.pep_description,
            "total_hours": round(r.total_hours or 0.0, 2),
            "actual_cost": round(r.actual_cost or 0.0, 2),
        }
        for r in rows
    ]


@router.get("/forecast", summary="Previsão de conclusão por PEP (EVM)", response_model=ForecastOut)
def get_forecast(
    db: DbSession,
    pep_wbs: str,
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 1.0

    project = db.query(Project).filter(Project.pep_wbs == pep_wbs).first()

    pep_desc_row = (
        db.query(TimesheetRecord.pep_description)
        .filter(TimesheetRecord.pep_wbs == pep_wbs, TimesheetRecord.pep_description.isnot(None))
        .first()
    )
    pep_description = pep_desc_row[0] if pep_desc_row else None

    q = (
        db.query(
            Cycle.name.label("cycle_name"),
            Cycle.start_date.label("cycle_start"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("period_hours"),
            func.sum(
                TimesheetRecord.cost_per_hour * (
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours * em
                    + TimesheetRecord.standby_hours * sm
                )
            ).label("period_cost"),
        )
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(
            TimesheetRecord.pep_wbs == pep_wbs,
            Cycle.is_quarantine == False,  # noqa: E712
        )
    )
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()

    if not rows:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para este PEP.")

    history = []
    cum_h = 0.0
    cum_c = 0.0
    for r in rows:
        cum_h += r.period_hours or 0.0
        cum_c += r.period_cost or 0.0
        history.append({
            "cycle_name": r.cycle_name,
            "cycle_start": r.cycle_start,
            "period_hours": round(r.period_hours or 0.0, 2),
            "period_cost": round(r.period_cost or 0.0, 2),
            "cumulative_hours": round(cum_h, 2),
            "cumulative_cost": round(cum_c, 2),
        })

    consumed_hours = cum_h
    actual_cost = cum_c

    recent = rows[-3:]
    avg_hours = sum(r.period_hours or 0.0 for r in recent) / len(recent) if recent else 0.0

    budget_hours = project.budget_hours if project else None
    budget_cost = project.budget_cost if project else None

    cpi = None
    eac = None
    if budget_hours and budget_cost and consumed_hours > 0 and actual_cost > 0:
        ev = (consumed_hours / budget_hours) * budget_cost
        cpi = round(ev / actual_cost, 3)
        eac = round(budget_cost / cpi, 2) if cpi > 0 else None

    remaining_hours = round(budget_hours - consumed_hours, 2) if budget_hours is not None else None

    est_cycles = None
    est_completion = None
    if remaining_hours is not None and remaining_hours > 0 and avg_hours > 0:
        est_cycles = round(remaining_hours / avg_hours, 1)
        n = math.ceil(est_cycles)
        future = (
            db.query(Cycle)
            .filter(
                Cycle.is_quarantine == False,  # noqa: E712
                Cycle.start_date > rows[-1].cycle_start,
            )
            .order_by(Cycle.start_date)
            .limit(n)
            .all()
        )
        if len(future) >= n:
            est_completion = future[n - 1].name

    return {
        "pep_wbs": pep_wbs,
        "pep_description": pep_description,
        "budget_hours": budget_hours,
        "budget_cost": budget_cost,
        "consumed_hours": round(consumed_hours, 2),
        "actual_cost": round(actual_cost, 2),
        "remaining_hours": remaining_hours,
        "cpi": cpi,
        "eac": eac,
        "avg_hours_per_cycle": round(avg_hours, 2),
        "estimated_cycles_to_complete": est_cycles,
        "estimated_completion_cycle": est_completion,
        "history": history,
    }
