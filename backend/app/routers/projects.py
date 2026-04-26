from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Project
from backend.app.schemas import ProjectIn

router = APIRouter(prefix="/api/projects", tags=["projects"])

DbSession = Annotated[Session, Depends(get_db)]


def _project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "pep_wbs": p.pep_wbs,
        "name": p.name,
        "client": p.client,
        "manager": p.manager,
        "budget_hours": p.budget_hours,
        "budget_cost": p.budget_cost,
        "status": p.status,
    }


@router.get("", summary="Listar projetos")
def list_projects(db: DbSession):
    projects = db.query(Project).order_by(Project.pep_wbs).all()
    return [_project_to_dict(p) for p in projects]


@router.post("", summary="Criar projeto", status_code=201)
def create_project(body: ProjectIn, db: DbSession):
    if db.query(Project).filter(Project.pep_wbs == body.pep_wbs).first():
        raise HTTPException(status_code=409, detail="Já existe um projeto com esse código PEP.")
    project = Project(**body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.put("/{project_id}", summary="Atualizar projeto")
def update_project(project_id: int, body: ProjectIn, db: DbSession):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    conflict = db.query(Project).filter(
        Project.pep_wbs == body.pep_wbs, Project.id != project_id
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Já existe outro projeto com esse código PEP.")
    for field, value in body.model_dump().items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.delete("/{project_id}", summary="Excluir projeto", status_code=204)
def delete_project(project_id: int, db: DbSession):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    db.delete(project)
    db.commit()
