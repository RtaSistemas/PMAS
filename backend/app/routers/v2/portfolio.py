"""GET /api/v2/portfolio — replaces /portfolio-health.

Reads from `pep_cycle_summary` (pre-computed at ingestion) and enriches with
Project budget data.  Returns render-ready fields including health classification
and CPI — zero computation needed in the frontend.
"""
from __future__ import annotations

from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import (
    Cycle, GlobalConfig, PepCycleSummary, Project, ProjectBaseline,
    TimesheetRecord, UserProjectAccess,
)
from backend.app.services.evm import classify_health, compute_cpi_ev, cpi_color, cpi_label, get_thresholds, resolve_effective_budget

router = APIRouter(prefix="/api/v2", tags=["v2"])

_HEALTH_COLOR = {
    "ok": "success",
    "warning": "warning",
    "critical": "danger",
    "overrun": "danger",
    "no_budget": "muted",
}


def _allowed_peps(db, user) -> list[str] | None:
    """Returns whitelist of pep_wbs or None (= unrestricted access)."""
    if user.role == "admin":
        return None
    accesses = (
        db.query(UserProjectAccess)
        .filter(UserProjectAccess.user_id == user.id)
        .all()
    )
    if not accesses:
        return None
    project_ids = [a.project_id for a in accesses]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    return [p.pep_wbs for p in projects]


@router.get("/portfolio", summary="Saúde do portfólio — render-ready com CPI e health por PEP", response_model=list)
def get_portfolio(
    db: DbSession,
    current_user=Depends(get_current_user),
    pep_wbs: List[str] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    cfg = db.get(GlobalConfig, 1)
    warning_threshold, critical_threshold = get_thresholds(cfg)

    allowed = _allowed_peps(db, current_user)

    q = db.query(PepCycleSummary).join(Cycle, PepCycleSummary.cycle_id == Cycle.id)
    if date_from:
        q = q.filter(Cycle.start_date >= date_from)
    if date_to:
        q = q.filter(Cycle.end_date <= date_to)
    if pep_wbs:
        q = q.filter(PepCycleSummary.pep_wbs.in_(pep_wbs))
    if allowed is not None:
        q = q.filter(PepCycleSummary.pep_wbs.in_(allowed))

    summaries = q.all()

    # Aggregate summary rows by pep_wbs
    by_pep: dict[str, dict] = {}
    for s in summaries:
        entry = by_pep.setdefault(s.pep_wbs, {
            "pep_wbs": s.pep_wbs,
            "pep_description": s.pep_description,
            "total_hours": 0.0,
            "total_cost": 0.0,
            "normal_cost": 0.0,
            "extra_cost": 0.0,
            "standby_cost": 0.0,
        })
        entry["total_hours"] += s.total_hours or 0.0
        entry["total_cost"]  += s.total_cost  or 0.0
        entry["normal_cost"] += s.normal_cost or 0.0
        entry["extra_cost"]  += s.extra_cost  or 0.0
        entry["standby_cost"] += s.standby_cost or 0.0

    if not by_pep:
        # Fallback: if summary tables are empty, serve from raw records
        return _portfolio_fallback(db, current_user, allowed, pep_wbs, date_from, date_to,
                                   warning_threshold, critical_threshold)

    # Enrich with Project + active Baseline
    all_pep_keys = list(by_pep.keys())
    projects = {p.pep_wbs: p for p in db.query(Project).filter(Project.pep_wbs.in_(all_pep_keys)).all()}
    active_baselines: dict[int, ProjectBaseline] = {}
    proj_ids = [p.id for p in projects.values()]
    if proj_ids:
        for bl in db.query(ProjectBaseline).filter(
            ProjectBaseline.project_id.in_(proj_ids),
            ProjectBaseline.is_active == True,  # noqa: E712
        ).all():
            active_baselines[bl.project_id] = bl

    result = []
    for pep_key, data in by_pep.items():
        proj = projects.get(pep_key)
        bl   = active_baselines.get(proj.id) if proj else None
        bh, bc = resolve_effective_budget(proj, bl)

        cpi        = compute_cpi_ev(data["total_hours"], bh, bc, data["total_cost"])
        h_health   = classify_health(data["total_hours"], bh, warning_threshold, critical_threshold)
        c_health   = classify_health(data["total_cost"],  bc, warning_threshold, critical_threshold)

        result.append({
            "pep_wbs":        pep_key,
            "pep_description": data["pep_description"],
            "name":           proj.name if proj else None,
            "budget_hours":   bh,
            "budget_cost":    bc,
            "total_hours":    round(data["total_hours"], 2),
            "total_cost":     round(data["total_cost"],  2),
            "normal_cost":    round(data["normal_cost"], 2),
            "extra_cost":     round(data["extra_cost"],  2),
            "standby_cost":   round(data["standby_cost"], 2),
            "cpi":            cpi,
            "cpi_label":      cpi_label(cpi),
            "cpi_color":      cpi_color(cpi),
            "health_hours":   h_health,
            "health_cost":    c_health,
            "health_hours_color": _HEALTH_COLOR[h_health],
            "health_cost_color":  _HEALTH_COLOR[c_health],
            "is_registered":  proj is not None,
        })

    result.sort(key=lambda x: x["total_hours"], reverse=True)
    return result


def _portfolio_fallback(db, current_user, allowed, pep_wbs_filter, date_from, date_to,
                        warning_threshold, critical_threshold):
    """Fallback to raw TimesheetRecord aggregation when summary tables are empty."""
    from sqlalchemy import func
    from backend.app.models import Collaborator

    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            func.sum(
                TimesheetRecord.normal_hours
                + TimesheetRecord.extra_hours
                + TimesheetRecord.standby_hours
            ).label("total_hours"),
            func.sum(
                func.coalesce(TimesheetRecord.normal_cost,  0.0)
                + func.coalesce(TimesheetRecord.extra_cost,   0.0)
                + func.coalesce(TimesheetRecord.standby_cost, 0.0)
            ).label("total_cost"),
            func.sum(TimesheetRecord.normal_cost).label("normal_cost"),
            func.sum(TimesheetRecord.extra_cost).label("extra_cost"),
            func.sum(TimesheetRecord.standby_cost).label("standby_cost"),
        )
        .filter(TimesheetRecord.pep_wbs.isnot(None))
    )
    if pep_wbs_filter:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_wbs_filter))
    if allowed is not None:
        q = q.filter(TimesheetRecord.pep_wbs.in_(allowed))
    if date_from:
        q = q.filter(TimesheetRecord.record_date >= date_from)
    if date_to:
        q = q.filter(TimesheetRecord.record_date <= date_to)

    rows = q.group_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description).all()

    by_pep: dict[str, dict] = {}
    for r in rows:
        entry = by_pep.setdefault(r.pep_wbs, {
            "pep_wbs": r.pep_wbs,
            "pep_description": r.pep_description,
            "total_hours": 0.0,
            "total_cost": 0.0,
            "normal_cost": 0.0,
            "extra_cost": 0.0,
            "standby_cost": 0.0,
        })
        entry["total_hours"]  += r.total_hours  or 0.0
        entry["total_cost"]   += r.total_cost   or 0.0
        entry["normal_cost"]  += r.normal_cost  or 0.0
        entry["extra_cost"]   += r.extra_cost   or 0.0
        entry["standby_cost"] += r.standby_cost or 0.0

    projects = {p.pep_wbs: p for p in db.query(Project).filter(
        Project.pep_wbs.in_(list(by_pep.keys()))
    ).all()}
    active_baselines: dict[int, ProjectBaseline] = {}
    proj_ids = [p.id for p in projects.values()]
    if proj_ids:
        for bl in db.query(ProjectBaseline).filter(
            ProjectBaseline.project_id.in_(proj_ids),
            ProjectBaseline.is_active == True,  # noqa: E712
        ).all():
            active_baselines[bl.project_id] = bl

    result = []
    for pep_key, data in by_pep.items():
        proj = projects.get(pep_key)
        bl   = active_baselines.get(proj.id) if proj else None
        bh, bc = resolve_effective_budget(proj, bl)
        cpi        = compute_cpi_ev(data["total_hours"], bh, bc, data["total_cost"])
        h_health   = classify_health(data["total_hours"], bh, warning_threshold, critical_threshold)
        c_health   = classify_health(data["total_cost"],  bc, warning_threshold, critical_threshold)
        result.append({
            "pep_wbs":        pep_key,
            "pep_description": data["pep_description"],
            "name":           proj.name if proj else None,
            "budget_hours":   bh,
            "budget_cost":    bc,
            "total_hours":    round(data["total_hours"],  2),
            "total_cost":     round(data["total_cost"],   2),
            "normal_cost":    round(data["normal_cost"],  2),
            "extra_cost":     round(data["extra_cost"],   2),
            "standby_cost":   round(data["standby_cost"], 2),
            "cpi":            cpi,
            "cpi_label":      cpi_label(cpi),
            "cpi_color":      cpi_color(cpi),
            "health_hours":   h_health,
            "health_cost":    c_health,
            "health_hours_color": _HEALTH_COLOR[h_health],
            "health_cost_color":  _HEALTH_COLOR[c_health],
            "is_registered":  proj is not None,
        })
    result.sort(key=lambda x: x["total_hours"], reverse=True)
    return result


@router.get("/portfolio/by-cycle", summary="Portfólio por ciclo — para timeline ECharts", response_model=list)
def get_portfolio_by_cycle(
    db: DbSession,
    current_user=Depends(get_current_user),
    pep_wbs: List[str] = Query(default=[]),
):
    """Returns portfolio data grouped by cycle for the ECharts timeline component.
    Covers all active (non-quarantine) cycles, ordered chronologically.
    """
    cfg = db.get(GlobalConfig, 1)
    warning_threshold, critical_threshold = get_thresholds(cfg)
    allowed = _allowed_peps(db, current_user)

    q = (
        db.query(PepCycleSummary)
        .join(Cycle, PepCycleSummary.cycle_id == Cycle.id)
        .filter(Cycle.is_active == True)  # noqa: E712  — excludes quarantine cycles
    )
    if pep_wbs:
        q = q.filter(PepCycleSummary.pep_wbs.in_(pep_wbs))
    if allowed is not None:
        q = q.filter(PepCycleSummary.pep_wbs.in_(allowed))

    summaries = q.all()
    if not summaries:
        return []

    # Collect cycle metadata
    cycle_ids = list({s.cycle_id for s in summaries})
    cycles_map = {c.id: c for c in db.query(Cycle).filter(Cycle.id.in_(cycle_ids)).all()}

    # Group summaries by cycle
    by_cycle: dict[int, dict] = {}
    for s in summaries:
        cyc = cycles_map[s.cycle_id]
        if s.cycle_id not in by_cycle:
            by_cycle[s.cycle_id] = {
                "cycle_id":    s.cycle_id,
                "cycle_name":  cyc.name,
                "cycle_start": str(cyc.start_date),
                "by_pep":      {},
            }
        entry = by_cycle[s.cycle_id]["by_pep"].setdefault(s.pep_wbs, {
            "pep_wbs":         s.pep_wbs,
            "pep_description": s.pep_description,
            "total_hours":     0.0,
            "total_cost":      0.0,
            "normal_cost":     0.0,
            "extra_cost":      0.0,
            "standby_cost":    0.0,
        })
        entry["total_hours"]  += s.total_hours  or 0.0
        entry["total_cost"]   += s.total_cost   or 0.0
        entry["normal_cost"]  += s.normal_cost  or 0.0
        entry["extra_cost"]   += s.extra_cost   or 0.0
        entry["standby_cost"] += s.standby_cost or 0.0

    # Bulk-load project + baseline data (once, shared across all cycles)
    all_pep_keys = list({pep for cdata in by_cycle.values() for pep in cdata["by_pep"]})
    projects = {p.pep_wbs: p for p in db.query(Project).filter(Project.pep_wbs.in_(all_pep_keys)).all()}
    active_baselines: dict[int, ProjectBaseline] = {}
    proj_ids = [p.id for p in projects.values()]
    if proj_ids:
        for bl in db.query(ProjectBaseline).filter(
            ProjectBaseline.project_id.in_(proj_ids),
            ProjectBaseline.is_active == True,  # noqa: E712
        ).all():
            active_baselines[bl.project_id] = bl

    def _enrich(data: dict) -> dict:
        pep_key = data["pep_wbs"]
        proj = projects.get(pep_key)
        bl   = active_baselines.get(proj.id) if proj else None
        bh, bc = resolve_effective_budget(proj, bl)
        cpi      = compute_cpi_ev(data["total_hours"], bh, bc, data["total_cost"])
        h_health = classify_health(data["total_hours"], bh, warning_threshold, critical_threshold)
        c_health = classify_health(data["total_cost"],  bc, warning_threshold, critical_threshold)
        return {
            "pep_wbs":            pep_key,
            "pep_description":    data["pep_description"],
            "name":               proj.name if proj else None,
            "budget_hours":       bh,
            "budget_cost":        bc,
            "total_hours":        round(data["total_hours"],  2),
            "total_cost":         round(data["total_cost"],   2),
            "normal_cost":        round(data["normal_cost"],  2),
            "extra_cost":         round(data["extra_cost"],   2),
            "standby_cost":       round(data["standby_cost"], 2),
            "cpi":                cpi,
            "cpi_label":          cpi_label(cpi),
            "cpi_color":          cpi_color(cpi),
            "health_hours":       h_health,
            "health_cost":        c_health,
            "health_hours_color": _HEALTH_COLOR[h_health],
            "health_cost_color":  _HEALTH_COLOR[c_health],
            "is_registered":      proj is not None,
        }

    result = []
    for cycle_id in sorted(by_cycle, key=lambda cid: cycles_map[cid].start_date):
        cdata = by_cycle[cycle_id]
        items = [_enrich(d) for d in cdata["by_pep"].values()]
        items.sort(key=lambda x: x["total_hours"], reverse=True)
        result.append({
            "cycle_id":    cycle_id,
            "cycle_name":  cdata["cycle_name"],
            "cycle_start": cdata["cycle_start"],
            "items":       items,
        })

    return result
