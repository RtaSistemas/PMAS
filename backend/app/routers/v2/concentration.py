"""GET /api/v2/concentration — Concentração de horas por colaborador por PEP (v2).

Usa colunas de custo frozen (normal_cost+extra_cost+standby_cost) em vez de
calcular cost_per_hour × weighted_hours inline.  ACL via _allowed_peps.

Retorna os mesmos campos da v1 (/api/portfolio-concentration).
"""
from __future__ import annotations

from datetime import date as DateType
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord
from backend.app.routers.v2.portfolio import _allowed_peps

router = APIRouter(prefix="/api/v2", tags=["v2"])


@router.get("/concentration", summary="Concentração de horas por colaborador por PEP (v2 — custo frozen)")
def get_concentration(
    db: DbSession,
    current_user=Depends(get_current_user),
    cycle_id: List[int] = Query(default=[]),
    pep_wbs: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
):
    # ACL filtering via _allowed_peps
    allowed = _allowed_peps(db, current_user)
    if allowed is not None:
        if pep_wbs:
            pep_wbs = [p for p in pep_wbs if p in allowed]
        else:
            pep_wbs = allowed

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
                TimesheetRecord.normal_cost
                + TimesheetRecord.extra_cost
                + TimesheetRecord.standby_cost
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

        top_contributors = []
        if len(sorted_contribs) <= 3:
            for name, hours in sorted_contribs:
                cost_val = contributors_cost.get(name, 0.0)
                top_contributors.append({
                    "name": name,
                    "hours": round(hours, 2),
                    "cost": round(cost_val, 2),
                    "pct": round(hours / total_hours * 100, 1),
                    "pct_cost": round(cost_val / total_cost * 100, 1) if total_cost > 0 else 0.0,
                })
        else:
            for name, hours in sorted_contribs[:3]:
                cost_val = contributors_cost.get(name, 0.0)
                top_contributors.append({
                    "name": name,
                    "hours": round(hours, 2),
                    "cost": round(cost_val, 2),
                    "pct": round(hours / total_hours * 100, 1),
                    "pct_cost": round(cost_val / total_cost * 100, 1) if total_cost > 0 else 0.0,
                })
            others_hours = sum(h for _, h in sorted_contribs[3:])
            others_cost  = sum(contributors_cost.get(n, 0.0) for n, _ in sorted_contribs[3:])
            others_count = len(sorted_contribs) - 3
            top_contributors.append({
                "name": f"Outros ({others_count})",
                "hours": round(others_hours, 2),
                "cost": round(others_cost, 2),
                "pct": round(others_hours / total_hours * 100, 1),
                "pct_cost": round(others_cost / total_cost * 100, 1) if total_cost > 0 else 0.0,
            })

        top1_pct = round(sorted_contribs[0][1] / total_hours * 100, 1)
        risk = "high" if top1_pct >= 60 else "medium" if top1_pct >= 40 else "low"

        # Cost-based top-1
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
            "top_contributors": top_contributors,
            "top1_pct": top1_pct,
            "top1_pct_cost": top1_pct_cost,
            "risk": risk,
            "risk_cost": risk_cost,
        })

    result.sort(key=lambda x: x["total_hours"], reverse=True)
    return result
