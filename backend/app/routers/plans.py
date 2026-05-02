from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import Cycle, Project, ProjectCyclePlan
from backend.app.schemas import IdOut, ProjectCyclePlanIn, ProjectCyclePlanOut

router = APIRouter(
    prefix="/api/projects",
    tags=["plans"],
    dependencies=[Depends(get_current_user)],
)


def _plan_to_dict(p: ProjectCyclePlan) -> dict:
    return {
        "id": p.id,
        "project_id": p.project_id,
        "cycle_id": p.cycle_id,
        "cycle_name": p.cycle.name,
        "planned_hours": p.planned_hours,
    }


@router.get("/{project_id}/plans", response_model=list[ProjectCyclePlanOut])
def list_plans(project_id: int, db: DbSession):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    plans = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id == project_id)
        .join(Cycle)
        .order_by(Cycle.start_date)
        .all()
    )
    return [_plan_to_dict(p) for p in plans]


@router.put("/{project_id}/plans/{cycle_id}", response_model=ProjectCyclePlanOut)
def upsert_plan(project_id: int, cycle_id: int, body: ProjectCyclePlanIn, db: DbSession, current_user: CurrentUser):
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    if db.get(Cycle, cycle_id) is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    plan = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id == project_id, ProjectCyclePlan.cycle_id == cycle_id)
        .first()
    )
    if plan is None:
        plan = ProjectCyclePlan(project_id=project_id, cycle_id=cycle_id, planned_hours=body.planned_hours)
        db.add(plan)
        db.flush()
        log_audit(db, current_user, "create", "project_plan", plan.id,
                  {"project_id": project_id, "cycle_id": cycle_id, "planned_hours": body.planned_hours})
    else:
        plan.planned_hours = body.planned_hours
        log_audit(db, current_user, "update", "project_plan", plan.id,
                  {"planned_hours": body.planned_hours})
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.delete("/{project_id}/plans/{cycle_id}", status_code=204)
def delete_plan(project_id: int, cycle_id: int, db: DbSession, current_user: CurrentUser):
    plan = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id == project_id, ProjectCyclePlan.cycle_id == cycle_id)
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    log_audit(db, current_user, "delete", "project_plan", plan.id,
              {"project_id": project_id, "cycle_id": cycle_id})
    db.delete(plan)
    db.commit()
