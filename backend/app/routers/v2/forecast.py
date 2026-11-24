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
from sqlalchemy import or_

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Cycle, GlobalConfig, PepCycleSummary, Project, ProjectBaseline, ProjectCyclePlan,
    TimesheetRecord,
)
from backend.app.routers.v2.portfolio import _allowed_peps, _check_date_range
from backend.app.services.evm import (
    classify_health,
    compute_cpi,
    compute_cv,
    compute_eac_from_ev,
    compute_eac_schedule,
    compute_earned_schedule,
    compute_ev_capped,
    compute_ieac_t,
    compute_period_delta,
    compute_period_delta_pct,
    compute_spi,
    compute_spi_t,
    compute_sv,
    compute_sv_t,
    compute_tcpi,
    compute_etc,
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
    tcpi_label,
    tcpi_status,
    vac_color,
    vac_label,
    get_thresholds,
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
    _check_date_range(date_from, date_to)
    allowed = _allowed_peps(db, current_user)
    if allowed is not None and pep_wbs not in allowed:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    cfg = db.get(GlobalConfig, 1)
    warning_threshold, critical_threshold = get_thresholds(cfg)

    project = db.query(Project).filter(Project.pep_wbs == pep_wbs).first()

    pep_desc_row = (
        db.query(TimesheetRecord.pep_description)
        .filter(TimesheetRecord.pep_wbs == pep_wbs, TimesheetRecord.pep_description.isnot(None))
        .first()
    )
    pep_description = pep_desc_row[0] if pep_desc_row else None

    # Load planned hours/cost/physical_pct per cycle
    plan_by_cycle_start: dict[DateType, float]        = {}
    plan_cost_by_cycle_start: dict[DateType, Optional[float]] = {}
    phys_pct_by_cycle_start: dict[DateType, float] = {}
    if project:
        plan_rows = (
            db.query(ProjectCyclePlan, Cycle.start_date)
            .join(Cycle, ProjectCyclePlan.cycle_id == Cycle.id)
            .filter(ProjectCyclePlan.project_id == project.id)
            .all()
        )
        plan_by_cycle_start      = {start: plan.planned_hours for plan, start in plan_rows}
        plan_cost_by_cycle_start = {start: plan.planned_cost  for plan, start in plan_rows}
        phys_pct_by_cycle_start  = {
            start: plan.physical_pct
            for plan, start in plan_rows
            if plan.physical_pct is not None
        }

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
    blended_rate = (budget_cost / budget_hours) if (budget_hours and budget_cost and budget_hours > 0) else None

    # Idle cycles (no hours for this PEP) are part of the timeline: elapsed time,
    # the 3-cycle velocity window and Earned Schedule all count calendar cycles.
    cycle_data = _fill_idle_cycles(
        db, cycle_data, [s for s, _ in sorted_plans], date_from, date_to,
    )

    def _planned_cost(start: DateType) -> Optional[float]:
        """Explicit planned cost, else planned hours x blended rate, else None."""
        if start not in plan_by_cycle_start:
            return None
        explicit = plan_cost_by_cycle_start.get(start)
        if explicit is not None:
            return explicit
        if blended_rate is not None:
            return round(plan_by_cycle_start[start] * blended_rate, 2)
        return None

    # Full planning timeline: actual cycles plus the plan cycles after the last actual.
    timeline = [start for _, start, _, _ in cycle_data]
    if has_plan and sorted_plans[-1][0] > timeline[-1]:
        last_start, last_plan = timeline[-1], sorted_plans[-1][0]
        future = {
            r[0] for r in db.query(Cycle.start_date).filter(
                Cycle.is_active == True,  # noqa: E712
                Cycle.start_date > last_start,
                Cycle.start_date <= last_plan,
            ).all()
        } | {s for s, _ in sorted_plans if s > last_start}
        timeline += sorted(future)

    has_plan_cost = has_plan and any(_planned_cost(s) is not None for s, _ in sorted_plans)
    # PV curve in R$ when a planned cost is known (explicit or derived) and EV is in R$;
    # otherwise the hours curve (AgileEVM proxy).
    pv_mode = "cost" if (has_plan_cost and budget_cost) else ("hours" if has_plan else None)
    pv_curve: list[float] = []
    run = 0.0
    for start in timeline:
        if pv_mode == "cost":
            run += _planned_cost(start) or 0.0
        elif pv_mode == "hours":
            run += plan_by_cycle_start.get(start, 0.0)
        pv_curve.append(round(run, 2))

    history = []
    cum_h   = 0.0
    cum_c   = 0.0
    cum_pc  = 0.0
    prev_period_h: Optional[float] = None
    prev_period_c: Optional[float] = None

    for i, (cyc_name, cyc_start, period_h, period_c) in enumerate(cycle_data):
        cum_h += period_h
        cum_c += period_c

        cum_ph = sum(h for s, h in sorted_plans if s <= cyc_start) if sorted_plans else 0.0
        pc_period = _planned_cost(cyc_start) if has_plan else None
        if pc_period is not None:
            cum_pc += pc_period

        cycle_phys_pct = phys_pct_by_cycle_start.get(cyc_start)
        if cycle_phys_pct is not None and budget_cost:
            ev_cost_cum = round(cycle_phys_pct * budget_cost, 2)
            ev_source   = "physical"
        else:
            ev_cost_cum = compute_ev_capped(cum_h, budget_hours, budget_cost)
            ev_source   = "hours"

        spi_cum = None
        if has_plan and cum_ph > 0:
            spi_cum = compute_spi(cum_ph, cum_h)

        sv_period = compute_sv(cum_h, cum_ph if has_plan else None)
        cv_period = compute_cv(ev_cost_cum, cum_c)

        h_delta     = compute_period_delta(period_h, prev_period_h)
        h_delta_pct = compute_period_delta_pct(period_h, prev_period_h)
        c_delta     = compute_period_delta(period_c, prev_period_c)
        c_delta_pct = compute_period_delta_pct(period_c, prev_period_c)

        # Earned Schedule at this cycle — against the FULL planned curve
        ev_for_es = ev_cost_cum if pv_mode == "cost" else cum_h
        es_i = compute_earned_schedule(ev_for_es, pv_curve) if pv_mode else None
        at_i = float(i + 1)

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
            "cumulative_planned_cost":   round(cum_pc, 2) if has_plan_cost else None,
            "cumulative_ev_cost":        ev_cost_cum,
            "cpi_cumulative":            compute_cpi(ev_cost_cum, cum_c),
            "ev_source":                 ev_source,
            "physical_pct":              cycle_phys_pct,
            "spi_cumulative":            spi_cum,
            "sv":                        sv_period,
            "sv_label":                  sv_label(sv_period),
            "sv_color":                  sv_color(sv_period),
            "cv":                        cv_period,
            "cv_label":                  cv_label(cv_period),
            "cv_color":                  cv_color(cv_period),
            "es":                        es_i,
            "spi_t":                     compute_spi_t(es_i, at_i),
            "sv_t":                      compute_sv_t(es_i, at_i),
        })
        prev_period_h = period_h
        prev_period_c = period_c

    at = len(cycle_data)          # actual time in cycles (calendar cycles, idle ones included)
    # planned duration = cycles from the timeline start to the last planned cycle
    pd_cycles = (
        len([s for s in timeline if s <= sorted_plans[-1][0]]) if has_plan else 0
    )

    es     = history[-1]["es"] if history else None
    spi_t  = compute_spi_t(es, at)
    sv_t   = compute_sv_t(es, at)
    ieac_t = compute_ieac_t(pd_cycles or None, spi_t)

    consumed_hours = cum_h
    actual_cost    = cum_c

    # Most recent cycle with a physical_pct declaration (walk backwards)
    last_physical_pct: Optional[float] = None
    for _, cyc_start, _, _ in reversed(cycle_data):
        if cyc_start in phys_pct_by_cycle_start:
            last_physical_pct = phys_pct_by_cycle_start[cyc_start]
            break
    uses_physical_pct = last_physical_pct is not None and bool(budget_cost)

    last_actual_h, last_planned_h = (
        freeze_spi_boundary([(s, h) for _, s, h, _ in cycle_data], sorted_plans)
        if has_plan else (None, None)
    )

    # VELOCITY WINDOW — 3 cycles (Forecast rule).
    # Using only the 3 most recent cycles keeps the velocity reactive to current
    # team rhythm without being distorted by ramp-up periods or past outliers.
    # Compare: Simulate uses min(6, N) for a smoother scenario base;
    #          Monte Carlo uses ALL non-zero cycles to model full variance.
    recent_h = [h for _, _, h, _ in cycle_data[-3:]]
    avg_hours = sum(recent_h) / len(recent_h) if recent_h else 0.0

    # Final EVM indicators
    ev_val = None
    cpi = spi = eac = eac_schedule = cv = tcpi = vac = sv = None
    tcpi_state: Optional[str] = None
    if budget_hours and budget_cost and consumed_hours > 0:
        ev_val = (
            round(last_physical_pct * budget_cost, 2)
            if uses_physical_pct
            else compute_ev_capped(consumed_hours, budget_hours, budget_cost)
        )
        # SPI computed first so schedule-sensitive EAC variant can use it
        if has_plan and last_planned_h and last_planned_h > 0:
            spi = compute_spi(last_planned_h, last_actual_h) if last_actual_h is not None else None
            sv  = compute_sv(last_actual_h or 0, last_planned_h)
        if actual_cost > 0 and ev_val is not None:
            cpi  = compute_cpi(ev_val, actual_cost)
            cv   = compute_cv(ev_val, actual_cost)
            tcpi = compute_tcpi(budget_cost, actual_cost, ev_val)
            tcpi_state = tcpi_status(budget_cost, actual_cost, ev_val)
        # EAC defaults to BAC when no performance data yet (R-14).  Computed from
        # unrounded EV/AC (not from the 4-decimal CPI) so EAC never drifts below AC.
        eac          = compute_eac_from_ev(budget_cost, ev_val, actual_cost, default_to_bac=True)
        eac_schedule = compute_eac_schedule(budget_cost, actual_cost, ev_val, cpi, spi)
        vac = compute_vac(budget_cost, eac)

    is_closed = (
        project is not None
        and project.status == "encerrado"
        and project.completion_date is not None
    )

    if uses_physical_pct and budget_hours:
        # Physical mode: remaining scope = (1 - pct) * budget_hours
        remaining_hours = round(max((1.0 - last_physical_pct) * budget_hours, 0.0), 2)
    else:
        remaining_hours = round(max(budget_hours - consumed_hours, 0.0), 2) if budget_hours else None
    remaining_cost  = compute_etc(eac, actual_cost)

    est_cycles = None
    est_completion = None
    if not is_closed and remaining_hours and remaining_hours > 0 and avg_hours > 0:
        # Use observed throughput only; SPI informs cost EAC, not cycle velocity
        effective_velocity = avg_hours
        raw_cycles = remaining_hours / effective_velocity
        est_cycles = round(raw_cycles, 1)                 # displayed value
        n = math.ceil(round(raw_cycles, 6))               # whole cycles from the unrounded value
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

    # Uncertainty band — same 3-cycle window as avg_hours (R-12).
    # Uses min/max throughput from that window to bound optimistic/pessimistic
    # cycle estimates; EAC band uses observed cost rate from the same 3 cycles.
    eac_low = eac_high = None
    est_cycles_optimistic = est_cycles_pessimistic = None
    if est_cycles is not None and remaining_hours and remaining_hours > 0:
        recent_data = cycle_data[-3:]
        h_vals = [h for _, _, h, _ in recent_data if h > 0]
        rates  = [c / h for _, _, h, c in recent_data if h > 0]
        if len(h_vals) >= 2:
            est_cycles_optimistic  = round(remaining_hours / max(h_vals), 1)
            est_cycles_pessimistic = round(remaining_hours / min(h_vals), 1)
        if len(rates) >= 2 and actual_cost > 0:
            eac_low  = round(actual_cost + remaining_hours * min(rates), 2)
            eac_high = round(actual_cost + remaining_hours * max(rates), 2)

    # For closed projects: freeze metrics at final state
    if is_closed:
        remaining_hours = 0.0
        remaining_cost  = 0.0
        tcpi            = None
        tcpi_state      = "complete"
        eac_schedule           = None
        est_cycles             = None
        est_completion         = None
        eac_low = eac_high     = None
        est_cycles_optimistic  = None
        est_cycles_pessimistic = None
        # EAC = AC (actual final cost, not a projection).  A closed project delivered
        # its whole scope, so EV = BAC: CV (EV - AC) and VAC (BAC - EAC) then agree.
        if actual_cost > 0:
            eac = round(actual_cost, 2)
            vac = compute_vac(budget_cost, eac)
            if budget_cost:
                ev_val = round(budget_cost, 2)
                cv  = compute_cv(ev_val, actual_cost)
                cpi = compute_cpi(ev_val, actual_cost)

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
        "eac_low":                    eac_low,
        "eac_high":                   eac_high,
        "eac_schedule":               eac_schedule,
        "eac_method":                 "cpi_spi" if eac_schedule is not None else "cpi",
        "vac":                        vac,
        "vac_label":                  vac_label(vac),
        "vac_color":                  vac_color(vac),
        "cv":                         cv,
        "cv_label":                   cv_label(cv),
        "cv_color":                   cv_color(cv),
        "tcpi":                       tcpi,
        "tcpi_color":                 tcpi_color(tcpi, tcpi_state),
        "tcpi_label":                 tcpi_label(tcpi, tcpi_state),
        "tcpi_status":                tcpi_state,
        "sv":                         sv,
        "sv_label":                   sv_label(sv),
        "sv_color":                   sv_color(sv),
        "avg_hours_per_cycle":        round(avg_hours, 2),
        "estimated_cycles_to_complete": est_cycles,
        "est_cycles_optimistic":      est_cycles_optimistic,
        "est_cycles_pessimistic":     est_cycles_pessimistic,
        "estimated_completion_cycle": est_completion,
        "uses_physical_pct":          uses_physical_pct,
        "last_physical_pct":          last_physical_pct,
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
        "es":                         es,
        "spi_t":                      spi_t,
        "spi_t_color":                spi_color(spi_t),
        "sv_t":                       sv_t,
        "ieac_t":                     ieac_t,
        "planned_duration_cycles":    pd_cycles if sorted_plans else None,
        "actual_time_cycles":         at,
    }


def _fill_idle_cycles(
    db,
    cycle_data: list[tuple[str, DateType, float, float]],
    plan_starts: list[DateType],
    date_from: Optional[DateType],
    date_to: Optional[DateType],
) -> list[tuple[str, DateType, float, float]]:
    """Add the cycles with no hours for the PEP (zero rows) between the first
    plan/actual cycle and the last actual cycle, ordered by start."""
    first, last = cycle_data[0][1], cycle_data[-1][1]
    anchor = min(first, plan_starts[0]) if plan_starts else first
    q = db.query(Cycle).filter(Cycle.start_date >= anchor, Cycle.start_date <= last)
    q = q.filter(or_(Cycle.is_active == True, Cycle.start_date.in_(plan_starts)))  # noqa: E712
    if date_from:
        q = q.filter(Cycle.start_date >= date_from)
    if date_to:
        q = q.filter(Cycle.end_date <= date_to)
    have = {start for _, start, _, _ in cycle_data}
    idle = [(c.name, c.start_date, 0.0, 0.0) for c in q.all() if c.start_date not in have]
    return sorted(cycle_data + idle, key=lambda x: x[1])


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
