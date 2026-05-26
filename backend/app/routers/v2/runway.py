"""GET /api/v2/runway — Runway do portfólio com custo frozen (v2).

Usa colunas de custo frozen (normal_cost+extra_cost+standby_cost) em vez de
calcular cost_per_hour × weighted_hours inline.  ACL via _allowed_peps.

Retorna os mesmos campos da v1 (/api/portfolio-runway).
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Cycle, GlobalConfig, Project, ProjectCyclePlan, TimesheetRecord,
)
from backend.app.routers.v2.portfolio import _allowed_peps
from backend.app.services.evm import compute_cpi_ev

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/runway", summary="Runway do portfólio: ciclos restantes por PEP (v2 — custo frozen)")
def get_runway(
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
    warning_threshold  = cfg.budget_warning_threshold  if cfg and hasattr(cfg, 'budget_warning_threshold')  else 0.9
    critical_threshold = cfg.budget_critical_threshold if cfg and hasattr(cfg, 'budget_critical_threshold') else 1.0

    # ACL filtering via _allowed_peps
    allowed = _allowed_peps(db, current_user)
    if allowed is not None:
        if pep_wbs:
            pep_wbs = [p for p in pep_wbs if p in allowed]
        else:
            pep_wbs = allowed

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
                TimesheetRecord.normal_cost
                + TimesheetRecord.extra_cost
                + TimesheetRecord.standby_cost
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
        from backend.app.models import Collaborator
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
    plans_by_project: dict[int, list] = defaultdict(list)
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
        is_closed = bool(
            proj and proj.status == "encerrado" and proj.completion_date is not None
        )

        # Use the last-3-cycles velocity window — exclude zero-value cycles from denominator
        sorted_cids = sorted(
            data["cycle_ids"],
            key=lambda cid: cycle_start_by_id.get(cid, __import__('datetime').date.min),
        )
        recent_cids = sorted_cids[-3:]
        recent_hours = [pep_cycle_hours.get(key, {}).get(cid, 0.0) for cid in recent_cids]
        recent_costs = [pep_cycle_costs.get(key, {}).get(cid, 0.0) for cid in recent_cids]

        recent_hours_nz = [h for h in recent_hours if h > 0]
        recent_costs_nz = [c for c in recent_costs if c > 0]
        avg_hours_per_cycle = sum(recent_hours_nz) / len(recent_hours_nz) if recent_hours_nz else 0.0
        avg_cost_per_cycle  = sum(recent_costs_nz) / len(recent_costs_nz) if recent_costs_nz else 0.0

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

            if not is_closed and avg_hours_per_cycle > 0 and remaining_hours is not None:
                cycles_to_complete = remaining_hours / avg_hours_per_cycle

                if remaining_hours > 0 and cycles_to_complete > 0:
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

        cpi = compute_cpi_ev(consumed_hours, budget_hours, budget_cost, actual_cost)

        # SPI — freeze EV/PV at the last plan cycle boundary
        spi = None
        schedule_status = "no_baseline"
        if proj and budget_hours and budget_cost:
            proj_plans_sorted = sorted(plans_by_project.get(proj.id, []), key=lambda x: x[0])
            if proj_plans_sorted:
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

        if pct_consumed_cost is None:
            cost_risk = "no_budget"
        elif pct_consumed_cost > 100:
            cost_risk = "overrun"
        elif pct_consumed_cost >= critical_threshold * 100:
            cost_risk = "critical"
        elif pct_consumed_cost >= warning_threshold * 100:
            cost_risk = "warning"
        else:
            cost_risk = "ok"

        result.append({
            "pep_wbs": key,
            "pep_description": data["pep_description"],
            "name": name,
            "is_closed": is_closed,
            "budget_hours": budget_hours,
            "budget_cost": round(budget_cost, 2) if budget_cost is not None else None,
            "consumed_hours": round(consumed_hours, 2),
            "actual_cost": round(actual_cost, 2),
            "pct_consumed": round(pct_consumed, 1) if pct_consumed is not None else None,
            "pct_consumed_cost": pct_consumed_cost,
            "avg_hours_per_cycle": round(avg_hours_per_cycle, 2),
            "avg_cost_per_cycle":  round(avg_cost_per_cycle,  2),
            "cycles_to_complete": None if is_closed else (round(cycles_to_complete, 1) if cycles_to_complete is not None and cycles_to_complete > 0 else None),
            "estimated_completion_cycle": None if is_closed else estimated_completion_cycle,
            "spi": spi,
            "schedule_status": schedule_status,
            "cpi": cpi,
            "risk": risk,
            "cost_risk": cost_risk,
        })

    result.sort(key=lambda x: x["consumed_hours"], reverse=True)
    return result
