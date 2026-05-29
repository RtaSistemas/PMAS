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
    compute_eac_schedule,
    compute_ev_capped,
    compute_period_delta,
    compute_period_delta_pct,
    compute_spi,
    compute_sv,
    compute_tcpi,
    compute_vac,
    cpi_color,
    cpi_label,
    cv_color,
    cv_label,
    freeze_spi_boundary,
    resolve_effective_budget,
    spi_color,
    spi_label,
    sv_color,
    sv_label,
    tcpi_color,
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
    budget_hours, budget_cost = resolve_effective_budget(project, active_baseline)

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
    prev_period_h: Optional[float] = None
    prev_period_c: Optional[float] = None

    for cyc_name, cyc_start, period_h, period_c in cycle_data:
        cum_h += period_h
        cum_c += period_c

        cum_ph = sum(h for s, h in sorted_plans if s <= cyc_start) if sorted_plans else 0.0
        pc_period = plan_cost_by_cycle_start.get(cyc_start) if has_plan else None
        # Derive planned cost from blended rate when no explicit cost baseline exists
        if pc_period is None and blended_rate is not None and cyc_start in plan_by_cycle_start:
            pc_period = round(plan_by_cycle_start[cyc_start] * blended_rate, 2)
        if pc_period is not None:
            cum_pc += pc_period

        ev_cost_cum = compute_ev_capped(cum_h, budget_hours, budget_cost)

        spi_cum = None
        if has_plan and cum_ph > 0:
            spi_cum = compute_spi(cum_ph, cum_h)

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
            "sv_label":                  sv_label(sv_period),
            "sv_color":                  sv_color(sv_period),
            "cv":                        cv_period,
            "cv_label":                  cv_label(cv_period),
            "cv_color":                  cv_color(cv_period),
        })
        prev_period_h = period_h
        prev_period_c = period_c

    consumed_hours = cum_h
    actual_cost    = cum_c

    last_actual_h, last_planned_h = (
        freeze_spi_boundary([(s, h) for _, s, h, _ in cycle_data], sorted_plans)
        if has_plan else (None, None)
    )

    recent_h = [h for _, _, h, _ in cycle_data[-3:]]
    avg_hours = sum(recent_h) / len(recent_h) if recent_h else 0.0

    # Final EVM indicators
    ev_val = None
    cpi = spi = eac = eac_schedule = cv = tcpi = vac = sv = None
    if budget_hours and budget_cost and consumed_hours > 0:
        ev_val = compute_ev_capped(consumed_hours, budget_hours, budget_cost)
        # SPI computed first so schedule-sensitive EAC variant can use it
        if has_plan and last_planned_h and last_planned_h > 0:
            spi = compute_spi(last_planned_h, last_actual_h) if last_actual_h is not None else None
            sv  = compute_sv(last_actual_h or 0, last_planned_h)
        if actual_cost > 0 and ev_val is not None:
            cpi  = compute_cpi(ev_val, actual_cost)
            cv   = compute_cv(ev_val, actual_cost)
            tcpi = compute_tcpi(budget_cost, actual_cost, ev_val)
        # EAC defaults to BAC when no performance data yet (R-14)
        eac          = compute_eac(budget_cost, cpi, default_to_bac=True)
        eac_schedule = compute_eac_schedule(budget_cost, actual_cost, ev_val, cpi, spi)
        vac = compute_vac(budget_cost, eac)

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
        # Use observed throughput only; SPI informs cost EAC, not cycle velocity
        effective_velocity = avg_hours
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
        eac_schedule    = None
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
        "cpi_label":                  cpi_label(cpi),
        "cpi_color":                  cpi_color(cpi),
        "spi":                        spi,
        "spi_label":                  spi_label(spi),
        "spi_color":                  spi_color(spi),
        "eac":                        eac,
        "eac_schedule":               eac_schedule,
        "eac_method":                 "cpi_spi" if eac_schedule is not None else "cpi",
        "vac":                        vac,
        "cv":                         cv,
        "tcpi":                       tcpi,
        "tcpi_color":                 tcpi_color(tcpi),
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

    # Fallback to raw records — use frozen cost columns to respect the EVM freeze pattern
    from sqlalchemy import func

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
                func.coalesce(TimesheetRecord.normal_cost,  0.0)
                + func.coalesce(TimesheetRecord.extra_cost,   0.0)
                + func.coalesce(TimesheetRecord.standby_cost, 0.0)
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
