"""GET /api/v2/forecast — replaces /api/forecast.

All EVM calculations (CPI, SPI, EAC, TCPI, VAC, CV, SV, delta) are performed
server-side via services/evm.py.  The response is render-ready: no arithmetic
required in the frontend.

Uses pep_cycle_summary for period costs when available, falling back to raw
TimesheetRecord aggregation for pre-migration data.
"""
from __future__ import annotations

import math
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Cycle, GlobalConfig, PepCycleSummary, Project, ProjectBaseline, ProjectCyclePlan,
    TimesheetRecord,
)
from backend.app.routers.v2.portfolio import _allowed_peps
from backend.app.services.evm import (
    classify_health,
    compute_cpi,
    compute_cv,
    compute_eac,
    compute_ev_cost,
    compute_period_delta,
    compute_period_delta_pct,
    compute_spi,
    compute_sv,
    compute_tcpi,
    compute_vac,
)

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/forecast", summary="Previsão EVM completa — render-ready com todos os indicadores")
def get_forecast(
    db: DbSession,
    current_user=Depends(get_current_user),
    pep_wbs: str = Query(...),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    allowed = _allowed_peps(db, current_user)
    if allowed is not None and pep_wbs not in allowed:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    cfg = db.get(GlobalConfig, 1)
    warning_threshold  = cfg.budget_warning_threshold  if cfg and hasattr(cfg, 'budget_warning_threshold')  else 0.9
    critical_threshold = cfg.budget_critical_threshold if cfg and hasattr(cfg, 'budget_critical_threshold') else 1.0

    project = db.query(Project).filter(Project.pep_wbs == pep_wbs).first()

    pep_desc_row = (
        db.query(TimesheetRecord.pep_description)
        .filter(TimesheetRecord.pep_wbs == pep_wbs, TimesheetRecord.pep_description.isnot(None))
        .first()
    )
    pep_description = pep_desc_row[0] if pep_desc_row else None

    # Load planned hours/cost per cycle
    plan_by_cycle_start: dict[DateType, float]        = {}
    plan_cost_by_cycle_start: dict[DateType, Optional[float]] = {}
    if project:
        plan_rows = (
            db.query(ProjectCyclePlan, Cycle.start_date)
            .join(Cycle, ProjectCyclePlan.cycle_id == Cycle.id)
            .filter(ProjectCyclePlan.project_id == project.id)
            .all()
        )
        plan_by_cycle_start      = {start: plan.planned_hours for plan, start in plan_rows}
        plan_cost_by_cycle_start = {start: plan.planned_cost  for plan, start in plan_rows}

    active_baseline = (
        db.query(ProjectBaseline).filter_by(project_id=project.id, is_active=True).first()
        if project else None
    )
    budget_hours = (active_baseline.budget_hours if active_baseline else None) or (project.budget_hours if project else None)
    budget_cost  = (active_baseline.budget_cost  if active_baseline else None) or (project.budget_cost  if project else None)

    # Build per-cycle actual data — prefer summary, fall back to raw
    cycle_data = _load_cycle_data(db, pep_wbs, date_from, date_to)

    if not cycle_data:
        raise HTTPException(status_code=404, detail="Nenhum dado encontrado para este PEP.")

    sorted_plans = sorted(plan_by_cycle_start.items()) if plan_by_cycle_start else []
    has_plan = bool(sorted_plans)
    has_any_planned_cost = has_plan and any(v is not None for v in plan_cost_by_cycle_start.values())
    blended_rate = (budget_cost / budget_hours) if (budget_hours and budget_cost and budget_hours > 0) else None

    history = []
    cum_h   = 0.0
    cum_c   = 0.0
    cum_pc  = 0.0
    prev_cum_ph = 0.0
    last_plan_ev: Optional[float] = None
    last_plan_pv: Optional[float] = None
    prev_period_h: Optional[float] = None
    prev_period_c: Optional[float] = None

    for cyc_name, cyc_start, period_h, period_c in cycle_data:
        cum_h += period_h
        cum_c += period_c

        cum_ph = sum(h for s, h in sorted_plans if s <= cyc_start) if sorted_plans else 0.0
        pc_period = plan_cost_by_cycle_start.get(cyc_start) if has_plan else None
        if pc_period is not None:
            cum_pc += pc_period

        ev_cost_cum = compute_ev_cost(cum_h, budget_cost, budget_hours)

        # BUG-A fix: freeze EV/PV at the last cycle where the plan advanced
        if has_plan and cum_ph > prev_cum_ph and budget_hours and budget_cost:
            last_plan_ev = min(cum_h  / budget_hours, 1.0) * budget_cost
            last_plan_pv = min(cum_ph / budget_hours, 1.0) * budget_cost
            prev_cum_ph = cum_ph

        spi_cum = None
        if has_plan and budget_hours and budget_cost and cum_ph > 0:
            ev_cum = min(cum_h  / budget_hours, 1.0) * budget_cost
            pv_cum = min(cum_ph / budget_hours, 1.0) * budget_cost
            if pv_cum > 0:
                spi_cum = round(ev_cum / pv_cum, 3)

        sv_period = compute_sv(cum_h, cum_ph if has_plan else None)
        cv_period = compute_cv(ev_cost_cum, cum_c)

        h_delta     = compute_period_delta(period_h, prev_period_h)
        h_delta_pct = compute_period_delta_pct(period_h, prev_period_h)
        c_delta     = compute_period_delta(period_c, prev_period_c)
        c_delta_pct = compute_period_delta_pct(period_c, prev_period_c)

        history.append({
            "cycle_name":                cyc_name,
            "cycle_start":               str(cyc_start),
            "period_hours":              round(period_h, 2),
            "period_cost":               round(period_c, 2),
            "period_hours_delta":        h_delta,
            "period_hours_delta_pct":    h_delta_pct,
            "period_cost_delta":         c_delta,
            "period_cost_delta_pct":     c_delta_pct,
            "cumulative_hours":          round(cum_h, 2),
            "cumulative_cost":           round(cum_c, 2),
            "planned_hours":             round(plan_by_cycle_start[cyc_start], 2) if cyc_start in plan_by_cycle_start else None,
            "planned_cost":              round(pc_period, 2) if pc_period is not None else None,
            "cumulative_planned_hours":  round(cum_ph, 2) if has_plan else None,
            "cumulative_planned_cost":   round(cum_pc, 2) if has_any_planned_cost else None,
            "cumulative_ev_cost":        ev_cost_cum,
            "spi_cumulative":            spi_cum,
            "sv":                        sv_period,
            "sv_label":                  _sv_label(sv_period),
            "sv_color":                  _sv_color(sv_period),
            "cv":                        cv_period,
            "cv_label":                  _cv_label(cv_period),
            "cv_color":                  _cv_color(cv_period),
        })
        prev_period_h = period_h
        prev_period_c = period_c

    consumed_hours = cum_h
    actual_cost    = cum_c

    recent_h = [h for _, _, h, _ in cycle_data[-3:]]
    avg_hours = sum(recent_h) / len(recent_h) if recent_h else 0.0

    # Final EVM indicators
    ev_val = None
    cpi = spi = eac = cv = tcpi = vac = sv = None
    if budget_hours and budget_cost and consumed_hours > 0:
        ev_val = min(consumed_hours / budget_hours, 1.0) * budget_cost
        if actual_cost > 0:
            cpi  = compute_cpi(ev_val, actual_cost)
            eac  = compute_eac(budget_cost, cpi)
            cv   = compute_cv(ev_val, actual_cost)
            tcpi = compute_tcpi(budget_cost, actual_cost, ev_val)
        vac = compute_vac(budget_cost, eac)
        if has_plan and last_plan_pv and last_plan_pv > 0:
            spi = compute_spi(last_plan_pv, last_plan_ev) if last_plan_ev is not None else None
            sv  = compute_sv(last_plan_ev or 0, last_plan_pv)

    is_closed = (
        project is not None
        and project.status == "encerrado"
        and project.completion_date is not None
    )

    remaining_hours = round(max(budget_hours - consumed_hours, 0.0), 2) if budget_hours else None
    remaining_cost  = round(eac - actual_cost, 2) if eac is not None else None

    est_cycles = None
    est_completion = None
    if not is_closed and remaining_hours and remaining_hours > 0 and avg_hours > 0:
        effective_velocity = avg_hours * spi if (spi and spi > 0) else avg_hours
        est_cycles = round(remaining_hours / effective_velocity, 1)
        n = math.ceil(est_cycles)
        last_start = cycle_data[-1][1]
        future = (
            db.query(Cycle)
            .filter(Cycle.start_date > last_start)
            .order_by(Cycle.start_date)
            .limit(n)
            .all()
        )
        if len(future) >= n:
            est_completion = future[n - 1].name

    # For closed projects: freeze metrics at final state
    if is_closed:
        remaining_hours = 0.0
        remaining_cost  = 0.0
        tcpi            = None
        est_cycles      = None
        est_completion  = None
        # EAC = AC (actual final cost, not a projection)
        if actual_cost > 0:
            eac = round(actual_cost, 2)
            vac = compute_vac(budget_cost, eac)
            cv  = compute_cv(ev_val, actual_cost)

    return {
        "pep_wbs":                    pep_wbs,
        "pep_description":            pep_description,
        "name":                       project.name if project else None,
        "budget_hours":               budget_hours,
        "budget_cost":                budget_cost,
        "consumed_hours":             round(consumed_hours, 2),
        "actual_cost":                round(actual_cost, 2),
        "remaining_hours":            remaining_hours,
        "remaining_cost":             remaining_cost,
        "cpi":                        cpi,
        "cpi_label":                  _cpi_label(cpi),
        "cpi_color":                  _cpi_color(cpi),
        "spi":                        spi,
        "spi_label":                  _spi_label(spi),
        "spi_color":                  _spi_color(spi),
        "eac":                        eac,
        "vac":                        vac,
        "cv":                         cv,
        "tcpi":                       tcpi,
        "sv":                         sv,
        "avg_hours_per_cycle":        round(avg_hours, 2),
        "estimated_cycles_to_complete": est_cycles,
        "estimated_completion_cycle": est_completion,
        "is_closed":                  is_closed,
        "start_date":                 str(project.start_date)       if (project and project.start_date)       else None,
        "planned_end_date":           str(project.planned_end_date) if (project and project.planned_end_date) else None,
        "completed_on":               str(project.completion_date)  if is_closed                              else None,
        "using_baseline":             active_baseline is not None,
        "baseline_locked_at":         active_baseline.locked_at if active_baseline else None,
        "baseline_label":             active_baseline.label if active_baseline else None,
        "health_hours":               classify_health(consumed_hours, budget_hours, warning_threshold, critical_threshold),
        "health_cost":                classify_health(actual_cost,    budget_cost,  warning_threshold, critical_threshold),
        "history":                    history,
    }


def _load_cycle_data(
    db, pep_wbs: str,
    date_from: Optional[DateType],
    date_to: Optional[DateType],
) -> list[tuple[str, DateType, float, float]]:
    """Return [(cycle_name, cycle_start, period_hours, period_cost)] ordered by start."""
    # Try summary table first
    summaries = (
        db.query(PepCycleSummary)
        .join(Cycle, PepCycleSummary.cycle_id == Cycle.id)
        .filter(PepCycleSummary.pep_wbs == pep_wbs)
    )
    if date_from:
        summaries = summaries.filter(Cycle.start_date >= date_from)
    if date_to:
        summaries = summaries.filter(Cycle.end_date <= date_to)
    summary_rows = summaries.all()

    if summary_rows:
        # Aggregate by cycle (multiple pep_description variants possible)
        by_cycle: dict[int, tuple] = {}
        for s in summary_rows:
            if s.cycle_id not in by_cycle:
                by_cycle[s.cycle_id] = (s.cycle.name, s.cycle.start_date, 0.0, 0.0)
            n, st, h, c = by_cycle[s.cycle_id]
            by_cycle[s.cycle_id] = (n, st, h + (s.total_hours or 0.0), c + (s.total_cost or 0.0))
        return sorted(by_cycle.values(), key=lambda x: x[1])

    # Fallback to raw records
    from sqlalchemy import func
    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier   if cfg else 1.5
    sm = cfg.standby_hours_multiplier if cfg else 0.33

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
        .filter(TimesheetRecord.pep_wbs == pep_wbs)
    )
    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()
    return [(r.cycle_name, r.cycle_start, r.period_hours or 0.0, r.period_cost or 0.0) for r in rows]


# ── Label/color helpers ──────────────────────────────────────────────────────

def _cpi_label(v): return ("Dentro do orçamento" if v >= 1 else "Acima do orçamento") if v else None
def _cpi_color(v): return ("success" if v >= 1 else "warning" if v >= 0.9 else "danger") if v else None
def _spi_label(v): return ("No prazo" if v >= 1 else "Atenção" if v >= 0.9 else "Atrasado") if v else None
def _spi_color(v): return ("success" if v >= 1 else "warning" if v >= 0.9 else "danger") if v else None
def _sv_label(v):
    if v is None: return None
    if v > 0:  return f"Adiantado em {abs(v):.1f}h"
    if v < 0:  return f"Atrasado em {abs(v):.1f}h"
    return "No prazo"
def _sv_color(v):
    if v is None: return None
    return "success" if v >= 0 else "warning" if v >= -10 else "danger"
def _cv_label(v):
    if v is None: return None
    if v > 0:  return f"Economia de R$ {abs(v):,.2f}"
    if v < 0:  return f"Estouro de R$ {abs(v):,.2f}"
    return "No prazo"
def _cv_color(v):
    if v is None: return None
    return "success" if v >= 0 else "danger"
