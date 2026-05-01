from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import Project
from backend.app.schemas import ImportResultOut, ProjectIn, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


def _str_or_none(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in {"nan", "none", ""} else s


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    s = str(value).strip()
    if s.lower() in {"nan", "none", ""}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


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


@router.get("", summary="Listar projetos", response_model=list[ProjectOut])
def list_projects(db: DbSession):
    projects = db.query(Project).order_by(Project.pep_wbs).all()
    return [_project_to_dict(p) for p in projects]


@router.post("", summary="Criar projeto", status_code=201, response_model=ProjectOut)
def create_project(body: ProjectIn, db: DbSession, current_user: CurrentUser):
    if db.query(Project).filter(Project.pep_wbs == body.pep_wbs).first():
        raise HTTPException(status_code=409, detail="Já existe um projeto com esse código PEP.")
    project = Project(**body.model_dump())
    db.add(project)
    db.flush()
    log_audit(db, current_user, "create", "project", project.id, {"pep_wbs": project.pep_wbs, "name": project.name})
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.put("/{project_id}", summary="Atualizar projeto", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectIn, db: DbSession, current_user: CurrentUser):
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
    log_audit(db, current_user, "update", "project", project_id, body.model_dump())
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.post("/import", summary="Importar projetos via CSV", response_model=ImportResultOut)
def import_projects(file: UploadFile, db: DbSession, current_user: CurrentUser):
    try:
        df = pd.read_csv(io.BytesIO(file.file.read()))
        df.columns = [c.strip() for c in df.columns]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {e}")
    missing = {"pep_wbs"} - set(df.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {missing}")
    created, updated, errors = 0, 0, []
    for i, row in df.iterrows():
        try:
            pep = _str_or_none(row.get("pep_wbs"))
            if not pep:
                errors.append(f"Linha {i + 2}: pep_wbs vazio")
                continue
            name    = _str_or_none(row.get("name"))
            client  = _str_or_none(row.get("client"))
            manager = _str_or_none(row.get("manager"))
            raw_status = str(row.get("status", "ativo")).strip()
            status = raw_status if raw_status in ("ativo", "suspenso", "encerrado") else "ativo"
            budget_hours = _float_or_none(row.get("budget_hours"))
            budget_cost  = _float_or_none(row.get("budget_cost"))
            existing = db.query(Project).filter(Project.pep_wbs == pep).first()
            if existing:
                if name    is not None: existing.name         = name
                if client  is not None: existing.client       = client
                if manager is not None: existing.manager      = manager
                existing.status = status
                if budget_hours is not None: existing.budget_hours = budget_hours
                if budget_cost  is not None: existing.budget_cost  = budget_cost
                updated += 1
            else:
                db.add(Project(
                    pep_wbs=pep, name=name, client=client, manager=manager,
                    status=status, budget_hours=budget_hours, budget_cost=budget_cost,
                ))
                created += 1
        except Exception as exc:
            errors.append(f"Linha {i + 2}: {exc}")
    if created or updated:
        log_audit(db, current_user, "import", "project", detail={"created": created, "updated": updated, "errors": len(errors)})
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}


@router.delete("/{project_id}", summary="Excluir projeto", status_code=204)
def delete_project(project_id: int, db: DbSession, current_user: CurrentUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    log_audit(db, current_user, "delete", "project", project_id, {"pep_wbs": project.pep_wbs, "name": project.name})
    db.delete(project)
    db.commit()
