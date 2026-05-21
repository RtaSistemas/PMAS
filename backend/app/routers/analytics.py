from __future__ import annotations

import math
from collections import defaultdict
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, GlobalConfig, Project, ProjectCyclePlan, TimesheetRecord, UserProjectAccess
from backend.app.schemas import (
    AllocationItem,
    BurnHistoryPoint,
    ConcentrationContributor,
    ConcentrationItem,
    ForecastOut,
    PortfolioHealthItem,
    RunwayItem,
    TrendItem,
)

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
    sm = cfg.standby_hours_multiplier if cfg else 0.33

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
    sm = cfg.standby_hours_multiplier if cfg else 0.33

    q = (
        db.query(
            Cycle.id.label("cycle_id"),
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
            func.sum(
                TimesheetRecord.cost_per_hour * TimesheetRecord.normal_hours
            ).label("normal_cost"),
            func.sum(
                TimesheetRecord.cost_per_hour * TimesheetRecord.extra_hours * em
            ).label("extra_cost"),
            func.sum(
                TimesheetRecord.cost_per_hour * TimesheetRecord.standby_hours * sm
            ).label("standby_cost"),
        )
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Cycle.is_active == True)
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
    from collections import defaultdict
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
                TimesheetRecord.pep_wbs.in_(list(budgeted_projects.keys())),
                Cycle.is_active == True,
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

        # Build per-cycle consumed_hours per (cycle_id, pep_wbs)
        cycle_pep_consumed: dict[tuple, float] = defaultdict(float)
        cycle_pep_ac: dict[tuple, float] = defaultdict(float)
        for cr in cpi_rows:
            cycle_pep_consumed[(cr.cycle_id, cr.pep_wbs)] += cr.consumed_hours or 0.0
            cycle_pep_ac[(cr.cycle_id, cr.pep_wbs)] += cr.actual_cost or 0.0
    else:
        cycle_pep_consumed = {}
        cycle_pep_ac = {}

    # Cumulative CPI: accumulate consumed hours and AC per PEP across cycles ordered by start_date
    cumulative_per_pep: dict[str, float] = defaultdict(float)
    cumulative_ac_per_pep: dict[str, float] = defaultdict(float)

    result = []
    for r in rows:
        cpi = None
        if budgeted_projects:
            for pep_code in budgeted_projects:
                cumulative_per_pep[pep_code] += cycle_pep_consumed.get((r.cycle_id, pep_code), 0.0)
                cumulative_ac_per_pep[pep_code] += cycle_pep_ac.get((r.cycle_id, pep_code), 0.0)
            total_ev = 0.0
            total_ac = 0.0
            for pep_code, proj in budgeted_projects.items():
                consumed = cumulative_per_pep[pep_code]
                ac = cumulative_ac_per_pep[pep_code]
                if proj.budget_hours and proj.budget_hours > 0 and proj.budget_cost and ac > 0:
                    ev = min(consumed / proj.budget_hours, 1.0) * proj.budget_cost
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
            "normal_cost": r.normal_cost or 0.0,
            "extra_cost": r.extra_cost or 0.0,
            "standby_cost": r.standby_cost or 0.0,
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
    sm = cfg.standby_hours_multiplier if cfg else 0.33

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
    sm = cfg.standby_hours_multiplier if cfg else 0.33

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

    budget_hours = project.budget_hours if project else None
    budget_cost = project.budget_cost if project else None

    # Sort plan entries by start_date so cumulative PV is computed correctly
    # even when plan cycles have no actual data (BUG-B fix)
    sorted_plans = sorted(plan_by_cycle_start.items()) if plan_by_cycle_start else []
    has_plan = bool(sorted_plans)

    history = []
    cum_h = 0.0
    cum_c = 0.0
    prev_cum_ph = 0.0
    last_plan_ev: Optional[float] = None
    last_plan_pv: Optional[float] = None

    for r in rows:
        cum_h += r.period_hours or 0.0
        cum_c += r.period_cost or 0.0

        # Cumulative planned hours through all plan cycles up to this cycle's start_date
        cum_ph = sum(h for s, h in sorted_plans if s <= r.cycle_start) if sorted_plans else 0.0

        # Capture EV/PV at the last cycle where the plan advanced (BUG-A fix):
        # avoids SPI converging to 1.0 when project overruns past the plan end date
        if has_plan and cum_ph > prev_cum_ph and budget_hours and budget_cost:
            last_plan_ev = min(cum_h / budget_hours, 1.0) * budget_cost
            last_plan_pv = min(cum_ph / budget_hours, 1.0) * budget_cost
            prev_cum_ph = cum_ph

        ph_period = plan_by_cycle_start.get(r.cycle_start)
        history.append({
            "cycle_name": r.cycle_name,
            "cycle_start": r.cycle_start,
            "period_hours": round(r.period_hours or 0.0, 2),
            "period_cost": round(r.period_cost or 0.0, 2),
            "cumulative_hours": round(cum_h, 2),
            "cumulative_cost": round(cum_c, 2),
            "planned_hours": round(ph_period, 2) if ph_period is not None else None,
            "cumulative_planned_hours": round(cum_ph, 2) if has_plan else None,
        })

    consumed_hours = cum_h
    actual_cost = cum_c

    recent = rows[-3:]
    avg_hours = sum(r.period_hours or 0.0 for r in recent) / len(recent) if recent else 0.0

    cpi = None
    eac = None
    spi = None
    sv = None

    if budget_hours and budget_cost and consumed_hours > 0:
        ev_val = min(consumed_hours / budget_hours, 1.0) * budget_cost
        if actual_cost > 0:
            cpi = round(ev_val / actual_cost, 3)
            eac = round(budget_cost / cpi, 2) if cpi > 0 else None
        # BUG-A fix: use EV/PV frozen at the last planned cycle, not final totals;
        # prevents SPI from converging to 1.0 after the project overruns its schedule
        if has_plan and last_plan_pv and last_plan_pv > 0:
            spi = round(last_plan_ev / last_plan_pv, 3)
            sv = round(last_plan_ev - last_plan_pv, 2)

    # BUG-C fix: floor remaining_hours at 0 so overrun projects don't return negative values
    remaining_hours = round(max(budget_hours - consumed_hours, 0.0), 2) if budget_hours is not None else None

    est_cycles = None
    est_completion = None
    if remaining_hours is not None and remaining_hours > 0 and avg_hours > 0:
        est_cycles = round(remaining_hours / avg_hours, 1)
        n = math.ceil(est_cycles)
        future = (
            db.query(Cycle)
            .filter(
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


@router.get("/portfolio-runway", summary="Runway do portfólio: ciclos restantes por PEP", response_model=list[RunwayItem])
def get_portfolio_runway(
    db: DbSession,
    current_user=Depends(get_current_user),
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 0.33
    warning_threshold = cfg.budget_warning_threshold if cfg else 0.9
    critical_threshold = cfg.budget_critical_threshold if cfg else 1.0

    # ACL filtering: if user has project access entries, restrict to those PEPs
    if current_user.role != "admin":
        allowed = (
            db.query(Project.pep_wbs)
            .join(UserProjectAccess, UserProjectAccess.project_id == Project.id)
            .filter(UserProjectAccess.user_id == current_user.id)
            .all()
        )
        if allowed:
            allowed_peps = [r[0] for r in allowed]
            if pep_wbs:
                pep_wbs = [p for p in pep_wbs if p in allowed_peps]
            else:
                pep_wbs = allowed_peps

    # Query per (pep_wbs, pep_description, cycle_id) to get period hours/cost
    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            TimesheetRecord.cycle_id,
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
            TimesheetRecord.pep_wbs.isnot(None),
        )
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

    rows = q.group_by(
        TimesheetRecord.pep_wbs,
        TimesheetRecord.pep_description,
        TimesheetRecord.cycle_id,
    ).all()

    if not rows:
        return []

    # Aggregate per PEP — also keep per-cycle hours and costs for SPI + velocity window
    from collections import defaultdict
    pep_data: dict[str, dict] = {}
    pep_cycle_hours: dict[str, dict[int, float]] = {}  # pep_wbs → {cycle_id: hours}
    pep_cycle_costs: dict[str, dict[int, float]] = {}  # pep_wbs → {cycle_id: cost}
    for r in rows:
        key = r.pep_wbs
        if key not in pep_data:
            pep_data[key] = {
                "pep_wbs": r.pep_wbs,
                "pep_description": r.pep_description,
                "consumed_hours": 0.0,
                "actual_cost": 0.0,
                "cycle_ids": set(),
            }
            pep_cycle_hours[key] = {}
            pep_cycle_costs[key] = {}
        pep_data[key]["consumed_hours"] += r.period_hours or 0.0
        pep_data[key]["actual_cost"]    += r.period_cost  or 0.0
        pep_data[key]["cycle_ids"].add(r.cycle_id)
        cid = r.cycle_id
        pep_cycle_hours[key][cid] = pep_cycle_hours[key].get(cid, 0.0) + (r.period_hours or 0.0)
        pep_cycle_costs[key][cid] = pep_cycle_costs[key].get(cid, 0.0) + (r.period_cost  or 0.0)

    # Fetch projects for budget info
    projects = {
        p.pep_wbs: p
        for p in db.query(Project)
        .filter(Project.pep_wbs.in_(list(pep_data.keys())))
        .all()
    }

    # All active cycles ordered by start_date for estimated completion
    all_cycles = (
        db.query(Cycle)
        .order_by(Cycle.start_date)
        .all()
    )
    cycle_index_map = {c.id: i for i, c in enumerate(all_cycles)}
    cycle_start_by_id = {c.id: c.start_date for c in all_cycles}

    # Batch-fetch all ProjectCyclePlan entries for the relevant projects (avoid N+1)
    project_ids = [p.id for p in projects.values()]
    all_plans = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id.in_(project_ids))
        .all()
        if project_ids else []
    )
    # Group plans by project_id → list of (cycle_start_date, planned_hours)
    from collections import defaultdict as _defaultdict
    plans_by_project: dict[int, list] = _defaultdict(list)
    for plan in all_plans:
        c_start = cycle_start_by_id.get(plan.cycle_id)
        if c_start is not None:
            plans_by_project[plan.project_id].append((c_start, plan.planned_hours))

    result = []
    for key, data in pep_data.items():
        proj = projects.get(key)
        budget_hours = proj.budget_hours if proj else None
        budget_cost  = proj.budget_cost  if proj else None
        name         = proj.name         if proj else None

        consumed_hours = data["consumed_hours"]
        actual_cost    = data["actual_cost"]
        num_cycles     = len(data["cycle_ids"])

        # Use the last-3-cycles velocity window, matching get_forecast's avg_hours calculation.
        # This ensures "Ciclos restantes" is consistent between Runway table and Previsão tab.
        sorted_cids = sorted(
            data["cycle_ids"],
            key=lambda cid: cycle_start_by_id.get(cid, __import__('datetime').date.min),
        )
        recent_cids = sorted_cids[-3:]
        recent_hours = [pep_cycle_hours.get(key, {}).get(cid, 0.0) for cid in recent_cids]
        recent_costs = [pep_cycle_costs.get(key, {}).get(cid, 0.0) for cid in recent_cids]

        avg_hours_per_cycle = sum(recent_hours) / len(recent_hours) if recent_hours else 0.0
        avg_cost_per_cycle  = sum(recent_costs) / len(recent_costs) if recent_costs else 0.0

        pct_consumed       = None
        remaining_hours    = None
        cycles_to_complete = None
        cpi                = None
        risk               = "no_budget"
        estimated_completion_cycle = None

        if budget_hours is not None and budget_hours > 0:
            pct_consumed    = consumed_hours / budget_hours * 100
            remaining_hours = max(budget_hours - consumed_hours, 0.0)

            if pct_consumed > 100:
                risk = "overrun"
            elif pct_consumed >= critical_threshold * 100:
                risk = "critical"
            elif pct_consumed >= warning_threshold * 100:
                risk = "warning"
            else:
                risk = "ok"

            if avg_hours_per_cycle > 0 and remaining_hours is not None:
                cycles_to_complete = remaining_hours / avg_hours_per_cycle

                if remaining_hours > 0 and cycles_to_complete > 0:
                    # Find last cycle used by this PEP
                    pep_cycle_ids = data["cycle_ids"]
                    last_cycle_idx = max(
                        (cycle_index_map[cid] for cid in pep_cycle_ids if cid in cycle_index_map),
                        default=None,
                    )
                    if last_cycle_idx is not None:
                        n = math.ceil(cycles_to_complete)
                        target_idx = last_cycle_idx + n
                        if target_idx < len(all_cycles):
                            estimated_completion_cycle = all_cycles[target_idx].name

        if budget_hours and budget_hours > 0 and budget_cost and actual_cost > 0:
            ev = min(consumed_hours / budget_hours, 1.0) * budget_cost
            cpi = round(ev / actual_cost, 3)

        # SPI — same algorithm as get_forecast: freeze EV/PV at the last plan cycle
        # boundary to avoid convergence to 1.0 when project overruns its budget.
        # Requires per-cycle actual data (pep_cycle_hours) collected above.
        spi = None
        schedule_status = "no_baseline"
        if proj and budget_hours and budget_cost:
            proj_plans_sorted = sorted(plans_by_project.get(proj.id, []), key=lambda x: x[0])
            if proj_plans_sorted:
                plan_by_cstart = {s: h for s, h in proj_plans_sorted}
                pep_cids_sorted = sorted(
                    data["cycle_ids"],
                    key=lambda cid: cycle_start_by_id.get(cid, __import__('datetime').date.min),
                )
                running_h = 0.0
                prev_cum_ph = 0.0
                last_plan_ev: Optional[float] = None
                last_plan_pv: Optional[float] = None
                for cid in pep_cids_sorted:
                    c_start = cycle_start_by_id.get(cid)
                    if c_start is None:
                        continue
                    running_h += pep_cycle_hours.get(key, {}).get(cid, 0.0)
                    cum_ph = sum(h for s, h in proj_plans_sorted if s <= c_start)
                    if cum_ph > prev_cum_ph:
                        last_plan_ev = min(running_h / budget_hours, 1.0) * budget_cost
                        last_plan_pv = min(cum_ph / budget_hours, 1.0) * budget_cost
                        prev_cum_ph = cum_ph

                if last_plan_pv and last_plan_pv > 0:
                    spi = round(last_plan_ev / last_plan_pv, 3)
                    if spi >= 1.0:
                        schedule_status = "on_track"
                    elif spi >= 0.9:
                        schedule_status = "at_risk"
                    else:
                        schedule_status = "behind"

        pct_consumed_cost = (
            round(actual_cost / budget_cost * 100, 1)
            if (budget_cost is not None and budget_cost > 0)
            else None
        )

        result.append({
            "pep_wbs": key,
            "pep_description": data["pep_description"],
            "name": name,
            "budget_hours": budget_hours,
            "budget_cost": round(budget_cost, 2) if budget_cost is not None else None,
            "consumed_hours": round(consumed_hours, 2),
            "actual_cost": round(actual_cost, 2),
            "pct_consumed": round(pct_consumed, 1) if pct_consumed is not None else None,
            "pct_consumed_cost": pct_consumed_cost,
            "avg_hours_per_cycle": round(avg_hours_per_cycle, 2),
            "avg_cost_per_cycle":  round(avg_cost_per_cycle,  2),
            "cycles_to_complete": round(cycles_to_complete, 1) if cycles_to_complete is not None and cycles_to_complete > 0 else None,
            "estimated_completion_cycle": estimated_completion_cycle,
            "spi": spi,
            "schedule_status": schedule_status,
            "cpi": cpi,
            "risk": risk,
        })

    result.sort(key=lambda x: x["consumed_hours"], reverse=True)
    return result


@router.get("/portfolio-concentration", summary="Concentração de horas por colaborador por PEP", response_model=list[ConcentrationItem])
def get_portfolio_concentration(
    db: DbSession,
    current_user=Depends(get_current_user),
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    # ACL filtering
    if current_user.role != "admin":
        allowed = (
            db.query(Project.pep_wbs)
            .join(UserProjectAccess, UserProjectAccess.project_id == Project.id)
            .filter(UserProjectAccess.user_id == current_user.id)
            .all()
        )
        if allowed:
            allowed_peps = [r[0] for r in allowed]
            if pep_wbs:
                pep_wbs = [p for p in pep_wbs if p in allowed_peps]
            else:
                pep_wbs = allowed_peps

    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            Collaborator.name.label("collaborator_name"),
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(
                (
                    TimesheetRecord.normal_hours
                    + TimesheetRecord.extra_hours
                    + TimesheetRecord.standby_hours
                ) * TimesheetRecord.cost_per_hour
            ).label("total_cost"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(
            TimesheetRecord.pep_wbs.isnot(None),
        )
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if pep_wbs:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(Collaborator.id.in_(collaborator_id))
    if date_from is not None:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to is not None:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(
        TimesheetRecord.pep_wbs,
        TimesheetRecord.pep_description,
        Collaborator.name,
    ).all()

    if not rows:
        return []

    # Aggregate per PEP
    from collections import defaultdict
    pep_contribs: dict[str, dict] = {}
    for r in rows:
        key = r.pep_wbs
        if key not in pep_contribs:
            pep_contribs[key] = {
                "pep_wbs": r.pep_wbs,
                "pep_description": r.pep_description,
                "contributors": {},
                "contributors_cost": {},
            }
        hours = r.total_hours or 0.0
        cost  = r.total_cost  or 0.0
        pep_contribs[key]["contributors"][r.collaborator_name] = (
            pep_contribs[key]["contributors"].get(r.collaborator_name, 0.0) + hours
        )
        pep_contribs[key]["contributors_cost"][r.collaborator_name] = (
            pep_contribs[key]["contributors_cost"].get(r.collaborator_name, 0.0) + cost
        )

    # Fetch project names
    projects = {
        p.pep_wbs: p
        for p in db.query(Project)
        .filter(Project.pep_wbs.in_(list(pep_contribs.keys())))
        .all()
    }

    result = []
    for key, data in pep_contribs.items():
        contributors      = data["contributors"]
        contributors_cost = data["contributors_cost"]
        total_hours = sum(contributors.values())
        total_cost  = sum(contributors_cost.values())
        if total_hours == 0:
            continue

        # Sort contributors by hours descending (primary ordering)
        sorted_contribs = sorted(contributors.items(), key=lambda x: x[1], reverse=True)

        def _make_contributor(name: str, hours: float) -> ConcentrationContributor:
            cost_val = contributors_cost.get(name, 0.0)
            return ConcentrationContributor(
                name=name,
                hours=round(hours, 2),
                cost=round(cost_val, 2),
                pct=round(hours / total_hours * 100, 1),
                pct_cost=round(cost_val / total_cost * 100, 1) if total_cost > 0 else 0.0,
            )

        top_contributors = []
        if len(sorted_contribs) <= 3:
            for name, hours in sorted_contribs:
                top_contributors.append(_make_contributor(name, hours))
        else:
            for name, hours in sorted_contribs[:3]:
                top_contributors.append(_make_contributor(name, hours))
            others_hours = sum(h for _, h in sorted_contribs[3:])
            others_cost  = sum(contributors_cost.get(n, 0.0) for n, _ in sorted_contribs[3:])
            others_count = len(sorted_contribs) - 3
            top_contributors.append(ConcentrationContributor(
                name=f"Outros ({others_count})",
                hours=round(others_hours, 2),
                cost=round(others_cost, 2),
                pct=round(others_hours / total_hours * 100, 1),
                pct_cost=round(others_cost / total_cost * 100, 1) if total_cost > 0 else 0.0,
            ))

        top1_pct = round(sorted_contribs[0][1] / total_hours * 100, 1)
        risk = "high" if top1_pct >= 60 else "medium" if top1_pct >= 40 else "low"

        # Cost-based top-1 — find contributor with highest cost share
        top1_cost_name = max(contributors_cost, key=lambda n: contributors_cost[n]) if contributors_cost else None
        top1_pct_cost  = round(contributors_cost[top1_cost_name] / total_cost * 100, 1) if (top1_cost_name and total_cost > 0) else 0.0
        risk_cost = "high" if top1_pct_cost >= 60 else "medium" if top1_pct_cost >= 40 else "low"

        proj = projects.get(key)
        result.append({
            "pep_wbs": key,
            "pep_description": data["pep_description"],
            "name": proj.name if proj else None,
            "total_hours": round(total_hours, 2),
            "total_cost": round(total_cost, 2),
            "top_contributors": [c.model_dump() for c in top_contributors],
            "top1_pct": top1_pct,
            "top1_pct_cost": top1_pct_cost,
            "risk": risk,
            "risk_cost": risk_cost,
        })

    result.sort(key=lambda x: x["total_hours"], reverse=True)
    return result
