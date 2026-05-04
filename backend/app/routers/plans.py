from __future__ import annotations

import io
import csv

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import Cycle, Project, ProjectCyclePlan
from backend.app.schemas import IdOut, ImportResultOut, ProjectCyclePlanIn, ProjectCyclePlanOut

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


@router.get("/{project_id}/plans/export", summary="Exportar baseline do projeto em CSV")
def export_plans(project_id: int, db: DbSession):
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
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["pep_wbs", "cycle_name", "planned_hours"])
    for p in plans:
        writer.writerow([project.pep_wbs, p.cycle.name, p.planned_hours])
    filename = f"baseline_{project.pep_wbs.replace('/', '-')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/plans/import", summary="Importar baseline de múltiplos projetos via CSV", response_model=ImportResultOut)
def import_plans(file: UploadFile, db: DbSession, current_user: CurrentUser):
    """CSV esperado: pep_wbs, cycle_name, planned_hours (cabeçalho obrigatório)."""
    try:
        text = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {exc}")

    required = {"pep_wbs", "cycle_name", "planned_hours"}
    if rows and not required.issubset(set(rows[0].keys())):
        missing = required - set(rows[0].keys())
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {missing}")

    # Pre-load indexes to avoid N+1 queries
    projects = {p.pep_wbs: p for p in db.query(Project).all()}
    cycles = {c.name: c for c in db.query(Cycle).all()}

    created = updated = 0
    errors: list[str] = []

    for i, row in enumerate(rows, start=2):
        pep = (row.get("pep_wbs") or "").strip()
        cname = (row.get("cycle_name") or "").strip()
        raw_h = (row.get("planned_hours") or "").strip()

        if not pep:
            errors.append(f"Linha {i}: pep_wbs vazio")
            continue
        if not cname:
            errors.append(f"Linha {i}: cycle_name vazio")
            continue
        try:
            hours = float(raw_h)
            if hours < 0:
                raise ValueError
        except ValueError:
            errors.append(f"Linha {i}: planned_hours inválido ({raw_h!r})")
            continue

        proj = projects.get(pep)
        if proj is None:
            errors.append(f"Linha {i}: projeto '{pep}' não encontrado")
            continue
        cycle = cycles.get(cname)
        if cycle is None:
            errors.append(f"Linha {i}: ciclo '{cname}' não encontrado")
            continue

        plan = (
            db.query(ProjectCyclePlan)
            .filter(ProjectCyclePlan.project_id == proj.id, ProjectCyclePlan.cycle_id == cycle.id)
            .first()
        )
        if plan is None:
            db.add(ProjectCyclePlan(project_id=proj.id, cycle_id=cycle.id, planned_hours=hours))
            created += 1
        else:
            plan.planned_hours = hours
            updated += 1

    if created or updated:
        log_audit(db, current_user, "import", "project_plan",
                  detail={"created": created, "updated": updated, "errors": len(errors)})
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}


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
