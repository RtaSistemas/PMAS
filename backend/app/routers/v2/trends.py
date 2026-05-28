"""GET /api/v2/trends — replaces /api/trends.

Reads from `pep_cycle_summary` for fast aggregation and enriches each cycle
with delta metrics (period-over-period) computed by services/evm.py.
All EVM computations are server-side; the frontend only renders.
"""
from __future__ import annotations

from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Cycle, GlobalConfig, PepCycleSummary, Project, TimesheetRecord
from backend.app.services.evm import compute_period_delta, compute_period_delta_pct

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/trends", summary="Tendências por ciclo com delta período-a-período", response_model=list)
def get_trends(
    db: DbSession,
    _=Depends(get_current_user),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    has_summaries = db.query(PepCycleSummary).first() is not None

    if has_summaries:
        return _trends_from_summary(db, pep_wbs, date_from, date_to)
    return _trends_fallback(db, pep_wbs, date_from, date_to)


def _trends_from_summary(db, pep_wbs_filter, date_from, date_to):
    q = (
        db.query(PepCycleSummary)
        .join(Cycle, PepCycleSummary.cycle_id == Cycle.id)
        .filter(Cycle.is_active == True)  # noqa: E712
    )
    if pep_wbs_filter:
        q = q.filter(PepCycleSummary.pep_wbs.in_(pep_wbs_filter))
    if date_from:
        q = q.filter(Cycle.start_date >= date_from)
    if date_to:
        q = q.filter(Cycle.end_date <= date_to)

    summaries = q.all()

    # Group by cycle
    cycle_map: dict[int, dict] = {}
    cycle_order: list[int] = []
    for s in summaries:
        if s.cycle_id not in cycle_map:
            cycle_map[s.cycle_id] = {
                "_cycle": s.cycle,
                "normal_hours": 0.0,
                "extra_hours": 0.0,
                "standby_hours": 0.0,
                "total_hours": 0.0,
                "total_cost": 0.0,
                "normal_cost": 0.0,
                "extra_cost": 0.0,
                "standby_cost": 0.0,
            }
            cycle_order.append(s.cycle_id)
        agg = cycle_map[s.cycle_id]
        agg["normal_hours"]  += s.normal_hours  or 0.0
        agg["extra_hours"]   += s.extra_hours   or 0.0
        agg["standby_hours"] += s.standby_hours or 0.0
        agg["total_hours"]   += s.total_hours   or 0.0
        agg["total_cost"]    += s.total_cost    or 0.0
        agg["normal_cost"]   += s.normal_cost   or 0.0
        agg["extra_cost"]    += s.extra_cost    or 0.0
        agg["standby_cost"]  += s.standby_cost  or 0.0

    # Sort by cycle start_date
    sorted_ids = sorted(cycle_order, key=lambda cid: cycle_map[cid]["_cycle"].start_date)

    result = []
    prev_hours:   float | None = None
    prev_cost:    float | None = None
    prev_normal_h: float | None = None
    prev_extra_h:  float | None = None
    prev_standby_h: float | None = None
    prev_normal_c: float | None = None
    prev_extra_c:  float | None = None
    prev_standby_c: float | None = None
    hours_window: list[float] = []
    cost_window:  list[float] = []
    for cid in sorted_ids:
        agg  = cycle_map[cid]
        cyc  = agg["_cycle"]
        th   = round(agg["total_hours"], 2)
        tc   = round(agg["total_cost"],  2)
        nh   = round(agg["normal_hours"],  2)
        eh   = round(agg["extra_hours"],   2)
        sh   = round(agg["standby_hours"], 2)
        nc   = round(agg["normal_cost"],   2)
        ec   = round(agg["extra_cost"],    2)
        sc   = round(agg["standby_cost"],  2)
        hours_window.append(th)
        cost_window.append(tc)
        if len(hours_window) > 3:
            hours_window.pop(0)
        if len(cost_window) > 3:
            cost_window.pop(0)
        result.append({
            "cycle_name":               cyc.name,
            "cycle_start":              str(cyc.start_date),
            "normal_hours":             nh,
            "extra_hours":              eh,
            "standby_hours":            sh,
            "total_hours":              th,
            "actual_cost":              tc,
            "normal_cost":              nc,
            "extra_cost":               ec,
            "standby_cost":             sc,
            "hours_delta":              compute_period_delta(th, prev_hours),
            "hours_delta_pct":          compute_period_delta_pct(th, prev_hours),
            "cost_delta":               compute_period_delta(tc, prev_cost),
            "cost_delta_pct":           compute_period_delta_pct(tc, prev_cost),
            "normal_hours_delta":       compute_period_delta(nh, prev_normal_h),
            "extra_hours_delta":        compute_period_delta(eh, prev_extra_h),
            "standby_hours_delta":      compute_period_delta(sh, prev_standby_h),
            "normal_hours_delta_pct":   compute_period_delta_pct(nh, prev_normal_h),
            "extra_hours_delta_pct":    compute_period_delta_pct(eh, prev_extra_h),
            "standby_hours_delta_pct":  compute_period_delta_pct(sh, prev_standby_h),
            "normal_cost_delta":        compute_period_delta(nc, prev_normal_c),
            "extra_cost_delta":         compute_period_delta(ec, prev_extra_c),
            "standby_cost_delta":       compute_period_delta(sc, prev_standby_c),
            "normal_cost_delta_pct":    compute_period_delta_pct(nc, prev_normal_c),
            "extra_cost_delta_pct":     compute_period_delta_pct(ec, prev_extra_c),
            "standby_cost_delta_pct":   compute_period_delta_pct(sc, prev_standby_c),
            "moving_avg_3_hours":       round(sum(hours_window) / len(hours_window), 2),
            "moving_avg_3_cost":        round(sum(cost_window)  / len(cost_window),  2),
        })
        prev_hours = th;    prev_cost = tc
        prev_normal_h = nh; prev_extra_h = eh;  prev_standby_h = sh
        prev_normal_c = nc; prev_extra_c = ec;  prev_standby_c = sc

    return result


def _trends_fallback(db, pep_wbs_filter, date_from, date_to):
    """Raw aggregation from TimesheetRecord when summary tables are empty."""
    from sqlalchemy import func

    cfg = db.get(GlobalConfig, 1)
    em = cfg.extra_hours_multiplier   if cfg else 1.5
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
        .join(Cycle, TimesheetRecord.cycle_id == Cycle.id)
        .filter(Cycle.is_active == True)  # noqa: E712
    )
    if pep_wbs_filter:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs_filter))
    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(Cycle.id).order_by(Cycle.start_date).all()

    result = []
    prev_hours:    float | None = None
    prev_cost:     float | None = None
    prev_normal_h: float | None = None
    prev_extra_h:  float | None = None
    prev_standby_h: float | None = None
    hours_window: list[float] = []
    cost_window:  list[float] = []
    for r in rows:
        th = round(r.total_hours  or 0.0, 2)
        tc = round(r.actual_cost  or 0.0, 2)
        nh = round(r.normal_hours  or 0.0, 2)
        eh = round(r.extra_hours   or 0.0, 2)
        sh = round(r.standby_hours or 0.0, 2)
        hours_window.append(th)
        cost_window.append(tc)
        if len(hours_window) > 3:
            hours_window.pop(0)
        if len(cost_window) > 3:
            cost_window.pop(0)
        result.append({
            "cycle_name":               r.cycle_name,
            "cycle_start":              str(r.cycle_start),
            "normal_hours":             nh,
            "extra_hours":              eh,
            "standby_hours":            sh,
            "total_hours":              th,
            "actual_cost":              tc,
            "normal_cost":              0.0,
            "extra_cost":               0.0,
            "standby_cost":             0.0,
            "hours_delta":              compute_period_delta(th, prev_hours),
            "hours_delta_pct":          compute_period_delta_pct(th, prev_hours),
            "cost_delta":               compute_period_delta(tc, prev_cost),
            "cost_delta_pct":           compute_period_delta_pct(tc, prev_cost),
            "normal_hours_delta":       compute_period_delta(nh, prev_normal_h),
            "extra_hours_delta":        compute_period_delta(eh, prev_extra_h),
            "standby_hours_delta":      compute_period_delta(sh, prev_standby_h),
            "normal_hours_delta_pct":   compute_period_delta_pct(nh, prev_normal_h),
            "extra_hours_delta_pct":    compute_period_delta_pct(eh, prev_extra_h),
            "standby_hours_delta_pct":  compute_period_delta_pct(sh, prev_standby_h),
            "normal_cost_delta":        None,
            "extra_cost_delta":         None,
            "standby_cost_delta":       None,
            "normal_cost_delta_pct":    None,
            "extra_cost_delta_pct":     None,
            "standby_cost_delta_pct":   None,
            "moving_avg_3_hours":       round(sum(hours_window) / len(hours_window), 2),
            "moving_avg_3_cost":        round(sum(cost_window)  / len(cost_window),  2),
        })
        prev_hours = th;    prev_cost = tc
        prev_normal_h = nh; prev_extra_h = eh; prev_standby_h = sh

    return result
