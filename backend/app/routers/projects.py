from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import BudgetRevision, Project, UserProjectAccess
from backend.app.schemas import BudgetRevisionOut, ImportResultOut, ProjectIn, ProjectOut, ProjectUpdateIn
from backend.app.utils import _str_or_none, now_br

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


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


def _date_or_none(value):
    if value is None:
        return None
    from datetime import date as _date
    if isinstance(value, _date):
        return value
    s = str(value).strip()
    if s.lower() in {"nan", "none", ""}:
        return None
    try:
        return _date.fromisoformat(s)
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
        "start_date":       p.start_date,
        "planned_end_date": p.planned_end_date,
        "completion_date":  p.completion_date,
    }


@router.get("", summary="Listar projetos", response_model=list[ProjectOut])
def list_projects(db: DbSession):
    projects = db.query(Project).order_by(Project.pep_wbs).all()
    return [_project_to_dict(p) for p in projects]


MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("", summary="Criar projeto", status_code=201, response_model=ProjectOut)
def create_project(body: ProjectIn, db: DbSession, current_user: AdminUser):
    if db.query(Project).filter(Project.pep_wbs == body.pep_wbs).first():
        raise HTTPException(status_code=409, detail="Já existe um projeto com esse código PEP.")
    project = Project(**body.model_dump())
    if project.completion_date is not None:
        project.status = "encerrado"
    db.add(project)
    db.flush()
    log_audit(db, current_user, "create", "project", project.id, {"pep_wbs": project.pep_wbs, "name": project.name})
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.put("/{project_id}", summary="Atualizar projeto", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectUpdateIn, db: DbSession, current_user: AdminUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    conflict = db.query(Project).filter(
        Project.pep_wbs == body.pep_wbs, Project.id != project_id
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="Já existe outro projeto com esse código PEP.")
    old_budget_hours = project.budget_hours
    old_budget_cost  = project.budget_cost
    for field, value in body.model_dump(exclude={"budget_change_reason"}).items():
        setattr(project, field, value)
    if project.completion_date is not None:
        project.status = "encerrado"
    if old_budget_hours != project.budget_hours or old_budget_cost != project.budget_cost:
        db.add(BudgetRevision(
            project_id=project_id,
            old_budget_hours=old_budget_hours,
            old_budget_cost=old_budget_cost,
            new_budget_hours=project.budget_hours,
            new_budget_cost=project.budget_cost,
            reason=body.budget_change_reason,
            changed_by=current_user.username,
            changed_at=now_br(),
        ))
    log_audit(db, current_user, "update", "project", project_id, body.model_dump(exclude={"budget_change_reason"}))
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@router.get("/{project_id}/budget-history", response_model=list[BudgetRevisionOut])
def get_budget_history(project_id: int, db: DbSession, current_user: CurrentUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    if current_user.role != "admin":
        accesses = (
            db.query(UserProjectAccess)
            .filter(UserProjectAccess.user_id == current_user.id)
            .all()
        )
        if accesses and not any(a.pep_wbs == project.pep_wbs for a in accesses):
            raise HTTPException(status_code=403, detail="Acesso negado.")
    return (
        db.query(BudgetRevision)
        .filter(BudgetRevision.project_id == project_id)
        .order_by(BudgetRevision.changed_at.desc())
        .all()
    )


@router.post("/import", summary="Importar projetos via CSV", response_model=ImportResultOut)
def import_projects(file: UploadFile, db: DbSession, current_user: AdminUser):
    try:
        raw = file.file.read()
        if len(raw) > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo CSV excede o limite de 10 MB.")
        df = pd.read_csv(io.BytesIO(raw))
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
            budget_hours     = _float_or_none(row.get("budget_hours"))
            budget_cost      = _float_or_none(row.get("budget_cost"))
            start_date       = _date_or_none(row.get("start_date"))
            planned_end_date = _date_or_none(row.get("planned_end_date"))
            completion_date  = _date_or_none(row.get("completion_date"))
            if completion_date is not None:
                status = "encerrado"
            existing = db.query(Project).filter(Project.pep_wbs == pep).first()
            if existing:
                if name    is not None: existing.name         = name
                if client  is not None: existing.client       = client
                if manager is not None: existing.manager      = manager
                existing.status = status
                if budget_hours     is not None: existing.budget_hours     = budget_hours
                if budget_cost      is not None: existing.budget_cost      = budget_cost
                if start_date       is not None: existing.start_date       = start_date
                if planned_end_date is not None: existing.planned_end_date = planned_end_date
                if completion_date  is not None: existing.completion_date  = completion_date
                updated += 1
            else:
                db.add(Project(
                    pep_wbs=pep, name=name, client=client, manager=manager,
                    status=status, budget_hours=budget_hours, budget_cost=budget_cost,
                    start_date=start_date, planned_end_date=planned_end_date,
                    completion_date=completion_date,
                ))
                created += 1
        except Exception as exc:
            errors.append(f"Linha {i + 2}: {exc}")
    if created or updated:
        log_audit(db, current_user, "import", "project", detail={"created": created, "updated": updated, "errors": len(errors)})
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}


@router.delete("/{project_id}", summary="Excluir projeto", status_code=204)
def delete_project(project_id: int, db: DbSession, current_user: AdminUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    log_audit(db, current_user, "delete", "project", project_id, {"pep_wbs": project.pep_wbs, "name": project.name})
    db.delete(project)
    db.commit()
