from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.database import DbSession
from backend.app.deps import get_current_user, require_admin
from backend.app.models import Project, ProjectBaseline
from backend.app.schemas import ProjectBaselineIn, ProjectBaselineOut

router = APIRouter(prefix="/api/projects", tags=["baselines"])


@router.post("/{project_id}/baseline", response_model=ProjectBaselineOut, dependencies=[Depends(get_current_user)])
def create_baseline(project_id: int, data: ProjectBaselineIn, db: DbSession, current_user=Depends(get_current_user)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    if project.budget_cost is None:
        raise HTTPException(status_code=400, detail="Defina o budget_cost do projeto antes de criar um baseline.")

    # Deactivate any existing active baseline for this project
    db.query(ProjectBaseline).filter_by(project_id=project_id, is_active=True).update({"is_active": False})

    baseline = ProjectBaseline(
        project_id=project_id,
        locked_by=current_user.username,
        budget_hours=project.budget_hours,
        budget_cost=project.budget_cost,
        label=data.label,
        is_active=True,
    )
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return baseline


@router.get("/{project_id}/baselines", response_model=List[ProjectBaselineOut], dependencies=[Depends(get_current_user)])
def list_baselines(project_id: int, db: DbSession):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    return (
        db.query(ProjectBaseline)
        .filter_by(project_id=project_id)
        .order_by(ProjectBaseline.locked_at.desc())
        .all()
    )


@router.delete("/{project_id}/baselines/{baseline_id}", dependencies=[Depends(require_admin)])
def delete_baseline(project_id: int, baseline_id: int, db: DbSession):
    bl = db.query(ProjectBaseline).filter_by(id=baseline_id, project_id=project_id).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Baseline não encontrado.")
    db.delete(bl)
    db.commit()
    return {"ok": True}


@router.post("/{project_id}/baselines/{baseline_id}/activate", response_model=ProjectBaselineOut, dependencies=[Depends(get_current_user)])
def activate_baseline(project_id: int, baseline_id: int, db: DbSession):
    """Reativa um baseline histórico como o baseline ativo do projeto."""
    bl = db.query(ProjectBaseline).filter_by(id=baseline_id, project_id=project_id).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Baseline não encontrado.")
    db.query(ProjectBaseline).filter_by(project_id=project_id, is_active=True).update({"is_active": False})
    bl.is_active = True
    db.commit()
    db.refresh(bl)
    return bl
