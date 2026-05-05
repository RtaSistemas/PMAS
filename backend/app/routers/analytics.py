from __future__ import annotations

import math
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, GlobalConfig, Project, ProjectCyclePlan, TimesheetRecord
from backend.app.schemas import AllocationItem, BurnHistoryPoint, ForecastOut, PortfolioHealthItem, TrendItem

router = APIRouter(prefix="/api", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/portfolio-health", summary="Horas consumidas por PEP com budget da tabela Project", response_model=list[PortfolioHealthItem])
def get_portfolio_health(
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
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        q = q.filter(Collaborator.id.in_(collaborator_id))
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
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        q = q.filter(Collaborator.id.in_(collaborator_id))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()

    # Weighted CPI: aggregate EV and AC only for PEPs that have budget_hours + budget_cost
    # and (when pep_wbs filter is set) match the filter.
    budgeted_projects = (
        db.query(Project)
        .filter(Project.budget_hours.isnot(None), Project.budget_cost.isnot(None))
    )
    if pep_wbs:
        budgeted_projects = budgeted_projects.filter(Project.pep_wbs.in_(pep_wbs))
    budgeted_projects = {p.pep_wbs: p for p in budgeted_projects.all()}

    # Per-cycle consumed hours for budgeted PEPs
    if budgeted_projects:
        cpi_q = (
            db.query(
                Cycle.id.label("cycle_id"),
                TimesheetRecord.pep_wbs,
                func.sum(
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours
                    + TimesheetRecord.standby_hours
                ).label("consumed_hours"),
                func.sum(
                    TimesheetRecord.cost_per_hour * (
                        TimesheetRecord.normal_hours
                        + TimesheetRecord.extra_hours * em
                        + TimesheetRecord.standby_hours * sm
                    )
                ).label("actual_cost"),
            )
            .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
            .filter(
                Cycle.is_quarantine == False,  # noqa: E712
                TimesheetRecord.pep_wbs.in_(list(budgeted_projects.keys())),
            )
        )
        if pep_description:
            cpi_q = cpi_q.filter(TimesheetRecord.pep_description.in_(pep_description))
        if collaborator_id:
            cpi_q = cpi_q.join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
            cpi_q = cpi_q.filter(Collaborator.id.in_(collaborator_id))
        if date_from is not None:
            cpi_q = cpi_q.filter(TimesheetRecord.record_date >= date_from)
        if date_to is not None:
            cpi_q = cpi_q.filter(TimesheetRecord.record_date <= date_to)
        cpi_rows = cpi_q.group_by(Cycle.id, TimesheetRecord.pep_wbs).all()

        # Build cumulative consumed_hours per (cycle_id, pep_wbs) for EV calculation
        from collections import defaultdict
        cycle_pep_consumed: dict[tuple, float] = defaultdict(float)
        cycle_pep_ac: dict[tuple, float] = defaultdict(float)
        for cr in cpi_rows:
            cycle_pep_consumed[(cr.cycle_id, cr.pep_wbs)] += cr.consumed_hours or 0.0
            cycle_pep_ac[(cr.cycle_id, cr.pep_wbs)] += cr.actual_cost or 0.0

        # Map cycle name → cycle id
        cycle_id_map = {r.cycle_name: None for r in rows}
        for c in db.query(Cycle).filter(Cycle.name.in_(list(cycle_id_map.keys()))).all():
            cycle_id_map[c.name] = c.id
    else:
        cycle_id_map = {}
        cycle_pep_consumed = {}
        cycle_pep_ac = {}

    result = []
    for r in rows:
        cpi = None
        if budgeted_projects and cycle_id_map.get(r.cycle_name):
            cid = cycle_id_map[r.cycle_name]
            total_ev = 0.0
            total_ac = 0.0
            for pep_code, proj in budgeted_projects.items():
                consumed = cycle_pep_consumed.get((cid, pep_code), 0.0)
                ac = cycle_pep_ac.get((cid, pep_code), 0.0)
                if proj.budget_hours and proj.budget_hours > 0 and proj.budget_cost:
                    ev = (consumed / proj.budget_hours) * proj.budget_cost
                    total_ev += ev
                    total_ac += ac
            if total_ac > 0:
                cpi = round(total_ev / total_ac, 3)
        result.append({
            "cycle_name": r.cycle_name,
            "normal_hours": r.normal_hours or 0.0,
            "extra_hours": r.extra_hours or 0.0,
            "standby_hours": r.standby_hours or 0.0,
            "actual_cost": r.actual_cost or 0.0,
            "cpi": cpi,
        })
    return result


@router.get("/allocation", summary="Matriz horas/custo por colaborador × PEP", response_model=list[AllocationItem])
def get_allocation(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
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
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
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

    # Load planned hours per cycle for this project (keyed by cycle start_date for alignment)
    plan_by_cycle_start: dict = {}
    if project:
        plan_rows = (
            db.query(ProjectCyclePlan, Cycle.start_date)
            .join(Cycle, ProjectCyclePlan.cycle_id == Cycle.id)
            .filter(ProjectCyclePlan.project_id == project.id)
            .all()
        )
        plan_by_cycle_start = {start: plan.planned_hours for plan, start in plan_rows}

    history = []
    cum_h = 0.0
    cum_c = 0.0
    cum_ph = 0.0
    has_plan = bool(plan_by_cycle_start)
    for r in rows:
        cum_h += r.period_hours or 0.0
        cum_c += r.period_cost or 0.0
        ph = plan_by_cycle_start.get(r.cycle_start)
        if ph is not None:
            cum_ph += ph
        history.append({
            "cycle_name": r.cycle_name,
            "cycle_start": r.cycle_start,
            "period_hours": round(r.period_hours or 0.0, 2),
            "period_cost": round(r.period_cost or 0.0, 2),
            "cumulative_hours": round(cum_h, 2),
            "cumulative_cost": round(cum_c, 2),
            "planned_hours": round(ph, 2) if ph is not None else None,
            "cumulative_planned_hours": round(cum_ph, 2) if has_plan else None,
        })

    consumed_hours = cum_h
    actual_cost = cum_c

    recent = rows[-3:]
    avg_hours = sum(r.period_hours or 0.0 for r in recent) / len(recent) if recent else 0.0

    budget_hours = project.budget_hours if project else None
    budget_cost = project.budget_cost if project else None

    cpi = None
    eac = None
    spi = None
    sv = None

    if budget_hours and budget_cost and consumed_hours > 0:
        ev_val = (consumed_hours / budget_hours) * budget_cost
        if actual_cost > 0:
            cpi = round(ev_val / actual_cost, 3)
            eac = round(budget_cost / cpi, 2) if cpi > 0 else None
        if has_plan and cum_ph > 0:
            pv_val = (cum_ph / budget_hours) * budget_cost
            spi = round(ev_val / pv_val, 3) if pv_val > 0 else None
            sv = round(ev_val - pv_val, 2)

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
        "spi": spi,
        "sv": sv,
        "avg_hours_per_cycle": round(avg_hours, 2),
        "estimated_cycles_to_complete": est_cycles,
        "estimated_completion_cycle": est_completion,
        "history": history,
    }
