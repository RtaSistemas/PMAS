from __future__ import annotations

import csv
import io
import math

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import Cycle, Project, ProjectCyclePlan
from backend.app.routers.projects import assert_project_access
from backend.app.schemas import IdOut, ImportResultOut, PhysicalProgressItem, ProjectCyclePlanIn, ProjectCyclePlanOut

router = APIRouter(
    prefix="/api/projects",
    tags=["plans"],
    dependencies=[Depends(get_current_user)],
)

MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB


def _plan_to_dict(p: ProjectCyclePlan) -> dict:
    return {
        "id": p.id,
        "project_id": p.project_id,
        "cycle_id": p.cycle_id,
        "cycle_name": p.cycle.name,
        "planned_hours": p.planned_hours,
        "planned_cost": p.planned_cost,
        "physical_pct": p.physical_pct,
        "physical_note": p.physical_note,
    }


@router.get("/{project_id}/plans", response_model=list[ProjectCyclePlanOut])
def list_plans(project_id: int, db: DbSession, current_user: CurrentUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    assert_project_access(db, current_user, project)
    plans = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id == project_id)
        .join(Cycle)
        .order_by(Cycle.start_date)
        .all()
    )
    return [_plan_to_dict(p) for p in plans]


@router.get("/{project_id}/plans/export", summary="Exportar baseline do projeto em CSV")
def export_plans(project_id: int, db: DbSession, current_user: CurrentUser):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    assert_project_access(db, current_user, project)
    plans = (
        db.query(ProjectCyclePlan)
        .filter(ProjectCyclePlan.project_id == project_id)
        .join(Cycle)
        .order_by(Cycle.start_date)
        .all()
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["pep_wbs", "cycle_name", "planned_hours", "planned_cost"])
    for p in plans:
        writer.writerow([project.pep_wbs, p.cycle.name, p.planned_hours,
                         "" if p.planned_cost is None else p.planned_cost])
    filename = f"baseline_{project.pep_wbs.replace('/', '-')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/plans/import", summary="Importar baseline de múltiplos projetos via CSV", response_model=ImportResultOut)
def import_plans(file: UploadFile, db: DbSession, current_user: AdminUser):
    """CSV esperado: pep_wbs, cycle_name, planned_hours (cabeçalho obrigatório)."""
    try:
        raw = file.file.read()
        if len(raw) > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo CSV excede o limite de 10 MB.")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {exc}")

    required = {"pep_wbs", "cycle_name", "planned_hours"}
    fieldnames = [(f or "").strip() for f in (reader.fieldnames or [])]
    if not fieldnames:
        raise HTTPException(status_code=422, detail="Arquivo CSV vazio.")
    missing = required - set(fieldnames)
    if missing:
        raise HTTPException(status_code=422, detail=f"Colunas obrigatórias ausentes: {sorted(missing)}")
    if not rows:
        return {"created": 0, "updated": 0, "errors": [],
                "message": "Arquivo sem linhas de dados: nada foi importado."}
    # Normalise header whitespace so " pep_wbs" still matches.
    rows = [{(k or "").strip(): v for k, v in r.items()} for r in rows]
    has_cost_col = "planned_cost" in fieldnames

    # Pre-load indexes to avoid N+1 queries
    projects = {p.pep_wbs: p for p in db.query(Project).all()}
    cycles = {c.name: c for c in db.query(Cycle).all()}
    cycles_ci = {}
    for c in db.query(Cycle).order_by(Cycle.id).all():
        cycles_ci.setdefault(c.name.strip().lower(), c)
    existing_plans = {
        (pl.project_id, pl.cycle_id): pl for pl in db.query(ProjectCyclePlan).all()
    }

    def _num(raw: str) -> float:
        v = float(raw)
        if not math.isfinite(v) or v < 0:
            raise ValueError
        return v

    created = updated = 0
    errors: list[str] = []
    seen: set[tuple[int, int]] = set()

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
            hours = _num(raw_h)
        except ValueError:
            errors.append(f"Linha {i}: planned_hours inválido ({raw_h!r})")
            continue

        cost: float | None = None
        if has_cost_col:
            raw_c = (row.get("planned_cost") or "").strip()
            if raw_c:
                try:
                    cost = _num(raw_c)
                except ValueError:
                    errors.append(f"Linha {i}: planned_cost inválido ({raw_c!r})")
                    continue

        proj = projects.get(pep)
        if proj is None:
            errors.append(f"Linha {i}: projeto '{pep}' não encontrado")
            continue
        cycle = cycles.get(cname) or cycles_ci.get(cname.lower())
        if cycle is None:
            errors.append(f"Linha {i}: ciclo '{cname}' não encontrado")
            continue

        key = (proj.id, cycle.id)
        if key in seen:
            errors.append(f"Linha {i}: linha duplicada para ('{pep}', '{cname}'); mantida a primeira ocorrência")
            continue
        seen.add(key)

        plan = existing_plans.get(key)
        if plan is None:
            new_plan = ProjectCyclePlan(project_id=proj.id, cycle_id=cycle.id,
                                        planned_hours=hours, planned_cost=cost)
            db.add(new_plan)
            existing_plans[key] = new_plan
            created += 1
        else:
            plan.planned_hours = hours
            if has_cost_col:
                plan.planned_cost = cost
            updated += 1

    if created or updated:
        log_audit(db, current_user, "import", "project_plan",
                  detail={"created": created, "updated": updated, "errors": len(errors)})
    db.commit()
    return {"created": created, "updated": updated, "errors": errors,
            "message": f"{created} criado(s), {updated} atualizado(s), {len(errors)} erro(s)."}


@router.put("/{project_id}/plans/{cycle_id}", response_model=ProjectCyclePlanOut)
def upsert_plan(project_id: int, cycle_id: int, body: ProjectCyclePlanIn, db: DbSession, current_user: AdminUser):
    if body.cycle_id != cycle_id:
        raise HTTPException(status_code=422, detail="cycle_id do corpo difere do ciclo informado na URL.")
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
        plan = ProjectCyclePlan(
            project_id=project_id, cycle_id=cycle_id,
            planned_hours=body.planned_hours, planned_cost=body.planned_cost,
            physical_pct=body.physical_pct, physical_note=body.physical_note,
        )
        db.add(plan)
        db.flush()
        log_audit(db, current_user, "create", "project_plan", plan.id,
                  {"project_id": project_id, "cycle_id": cycle_id,
                   "planned_hours": body.planned_hours, "planned_cost": body.planned_cost})
    else:
        plan.planned_hours = body.planned_hours
        plan.planned_cost  = body.planned_cost
        if body.physical_pct is not None or body.physical_note is not None:
            plan.physical_pct  = body.physical_pct
            plan.physical_note = body.physical_note
        log_audit(db, current_user, "update", "project_plan", plan.id,
                  {"planned_hours": body.planned_hours, "planned_cost": body.planned_cost})
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


@router.patch("/{project_id}/plans/physical-progress", response_model=list[ProjectCyclePlanOut])
def update_physical_progress(
    project_id: int,
    body: list[PhysicalProgressItem],
    db: DbSession,
    current_user: AdminUser,
):
    """Bulk-update physical_pct and physical_note for one or more cycles of a project."""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    updated_plans = []
    for item in body:
        plan = (
            db.query(ProjectCyclePlan)
            .filter(ProjectCyclePlan.project_id == project_id, ProjectCyclePlan.cycle_id == item.cycle_id)
            .first()
        )
        if plan is None:
            raise HTTPException(
                status_code=404,
                detail=f"Plano não encontrado para ciclo {item.cycle_id}.",
            )
        plan.physical_pct  = item.physical_pct
        plan.physical_note = item.physical_note
        updated_plans.append(plan)
    if updated_plans:
        log_audit(db, current_user, "update", "project_plan_physical", project_id,
                  {"cycles": [i.cycle_id for i in body]})
    db.commit()
    for p in updated_plans:
        db.refresh(p)
    return [_plan_to_dict(p) for p in updated_plans]


@router.delete("/{project_id}/plans/{cycle_id}", status_code=204)
def delete_plan(project_id: int, cycle_id: int, db: DbSession, current_user: AdminUser):
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
