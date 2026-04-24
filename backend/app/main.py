from __future__ import annotations

import logging
import os
import sys
from datetime import date as DateType
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db, init_db
from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord
from backend.app.services.ingestion import ingest_file

log = logging.getLogger(__name__)

app = FastAPI(
    title="PMAS API",
    description="Project Management Assistant System — Timesheet Foundation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _frontend_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "frontend")
    return os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


app.mount("/frontend", StaticFiles(directory=_frontend_dir(), html=True), name="frontend")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/frontend/index.html")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    log.info("PMAS API pronta. Banco inicializado.")


DbSession = Annotated[Session, Depends(get_db)]

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CycleIn(BaseModel):
    name: str
    start_date: DateType
    end_date: DateType

class ProjectIn(BaseModel):
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    budget_hours: Optional[float] = None
    status: str = "ativo"

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.post("/api/upload-timesheet", summary="Ingerir CSV ou XLSX de timesheet")
def upload_timesheet(file: UploadFile, db: DbSession):
    fname = file.filename or ""
    if not any(fname.lower().endswith(ext) for ext in (".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv ou .xlsx são aceitos.")

    contents = file.file.read()
    try:
        summary = ingest_file(contents, fname, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Erro inesperado durante ingestão.")
        raise HTTPException(status_code=500, detail="Erro interno durante ingestão.") from exc

    return {"status": "ok", **summary}

# ---------------------------------------------------------------------------
# Cycles — list + CRUD
# ---------------------------------------------------------------------------

def _cycle_record_counts(db: Session) -> dict[int, int]:
    rows = (
        db.query(TimesheetRecord.cycle_id, func.count(TimesheetRecord.id))
        .group_by(TimesheetRecord.cycle_id)
        .all()
    )
    return {cycle_id: cnt for cycle_id, cnt in rows}


@app.get("/api/cycles", summary="Listar ciclos")
def list_cycles(db: DbSession):
    cycles = db.query(Cycle).order_by(Cycle.start_date).all()
    counts = _cycle_record_counts(db)
    return [
        {
            "id": c.id,
            "name": c.name,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "is_quarantine": c.is_quarantine,
            "record_count": counts.get(c.id, 0),
        }
        for c in cycles
    ]


@app.post("/api/cycles", summary="Criar ciclo", status_code=201)
def create_cycle(body: CycleIn, db: DbSession):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    cycle = Cycle(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        is_quarantine=False,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return {
        "id": cycle.id,
        "name": cycle.name,
        "start_date": cycle.start_date.isoformat(),
        "end_date": cycle.end_date.isoformat(),
        "is_quarantine": cycle.is_quarantine,
        "record_count": 0,
    }


@app.put("/api/cycles/{cycle_id}", summary="Atualizar ciclo")
def update_cycle(cycle_id: int, body: CycleIn, db: DbSession):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="end_date deve ser >= start_date.")
    cycle.name = body.name
    cycle.start_date = body.start_date
    cycle.end_date = body.end_date
    db.commit()
    db.refresh(cycle)
    counts = _cycle_record_counts(db)
    return {
        "id": cycle.id,
        "name": cycle.name,
        "start_date": cycle.start_date.isoformat(),
        "end_date": cycle.end_date.isoformat(),
        "is_quarantine": cycle.is_quarantine,
        "record_count": counts.get(cycle.id, 0),
    }


@app.delete("/api/cycles/{cycle_id}", summary="Excluir ciclo", status_code=204)
def delete_cycle(cycle_id: int, db: DbSession):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")
    count = db.query(func.count(TimesheetRecord.id)).filter(
        TimesheetRecord.cycle_id == cycle_id
    ).scalar()
    if count:
        raise HTTPException(
            status_code=409,
            detail=f"Ciclo possui {count} registro(s). Remova os registros antes de excluir o ciclo.",
        )
    db.delete(cycle)
    db.commit()

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

@app.get("/api/collaborators", summary="Listar colaboradores")
def list_collaborators(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
):
    q = db.query(Collaborator.id, Collaborator.name).join(
        TimesheetRecord, TimesheetRecord.collaborator_id == Collaborator.id
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))

    rows = q.distinct().order_by(Collaborator.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]


@app.get("/api/peps", summary="Listar PEPs únicos")
def list_peps(
    db: DbSession,
    cycle_id: List[int] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
):
    q = db.query(
        TimesheetRecord.pep_wbs,
        TimesheetRecord.pep_description,
        func.count().label("n"),
    )
    if cycle_id:
        q = q.filter(TimesheetRecord.cycle_id.in_(cycle_id))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))

    rows = (
        q.filter(TimesheetRecord.pep_wbs.isnot(None))
        .group_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description)
        .order_by(TimesheetRecord.pep_wbs, TimesheetRecord.pep_description)
        .all()
    )

    from collections import defaultdict
    grouped: dict[str, dict] = defaultdict(lambda: {"code": "", "descriptions": [], "total_records": 0})
    for r in rows:
        code = r.pep_wbs
        grouped[code]["code"] = code
        grouped[code]["total_records"] += r.n
        if r.pep_description and r.pep_description not in grouped[code]["descriptions"]:
            grouped[code]["descriptions"].append(r.pep_description)

    return sorted(grouped.values(), key=lambda x: x["total_records"], reverse=True)

# ---------------------------------------------------------------------------
# Projects — CRUD
# ---------------------------------------------------------------------------

def _project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "pep_wbs": p.pep_wbs,
        "name": p.name,
        "client": p.client,
        "manager": p.manager,
        "budget_hours": p.budget_hours,
        "status": p.status,
    }


def _compute_budget_vs_actual(
    db: Session,
    pep_codes: List[str],
    cycle_id: Optional[int] = None,
    collaborator_ids: Optional[List[int]] = None,
) -> list:
    if pep_codes:
        projects = (
            db.query(Project)
            .filter(Project.pep_wbs.in_(pep_codes), Project.budget_hours.isnot(None))
            .all()
        )
    else:
        projects = db.query(Project).filter(Project.budget_hours.isnot(None)).all()

    if not projects:
        return []

    budget_peps = [p.pep_wbs for p in projects]
    q = (
        db.query(
            TimesheetRecord.pep_wbs,
            func.sum(
                TimesheetRecord.normal_hours + TimesheetRecord.extra_hours + TimesheetRecord.standby_hours
            ).label("total_hours"),
        )
        .filter(TimesheetRecord.pep_wbs.in_(budget_peps))
    )
    if cycle_id is not None:
        q = q.filter(TimesheetRecord.cycle_id == cycle_id)
    if collaborator_ids:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_ids))

    actual_by_pep = {
        r.pep_wbs: r.total_hours or 0.0
        for r in q.group_by(TimesheetRecord.pep_wbs).all()
    }

    return sorted(
        [
            {
                "pep_wbs": p.pep_wbs,
                "name": p.name,
                "budget_hours": p.budget_hours,
                "actual_hours": actual_by_pep.get(p.pep_wbs, 0.0),
            }
            for p in projects
        ],
        key=lambda x: x["budget_hours"],
        reverse=True,
    )


@app.get("/api/projects", summary="Listar projetos")
def list_projects(db: DbSession):
    projects = db.query(Project).order_by(Project.pep_wbs).all()
    return [_project_to_dict(p) for p in projects]


@app.post("/api/projects", summary="Criar projeto", status_code=201)
def create_project(body: ProjectIn, db: DbSession):
    if db.query(Project).filter(Project.pep_wbs == body.pep_wbs).first():
        raise HTTPException(status_code=409, detail="Já existe um projeto com esse código PEP.")
    project = Project(**body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@app.put("/api/projects/{project_id}", summary="Atualizar projeto")
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


@app.delete("/api/projects/{project_id}", summary="Excluir projeto", status_code=204)
def delete_project(project_id: int, db: DbSession):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    db.delete(project)
    db.commit()

# ---------------------------------------------------------------------------
# Dashboard (with filters)
# ---------------------------------------------------------------------------

@app.get("/api/dashboard", summary="Dashboard sem filtro de ciclo — toda a base")
def get_dashboard_all(
    db: DbSession,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
):
    q = (
        db.query(
            Collaborator.id.label("collaborator_id"),
            Collaborator.name.label("collaborator"),
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
    )

    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))

    rows = (
        q.group_by(TimesheetRecord.collaborator_id)
        .order_by(Collaborator.name)
        .all()
    )

    from collections import defaultdict
    per_collab: dict[str, dict] = defaultdict(
        lambda: {"normal_hours": 0.0, "extra_hours": 0.0, "standby_hours": 0.0}
    )
    for r in rows:
        per_collab[r.collaborator]["normal_hours"]  += r.normal_hours or 0.0
        per_collab[r.collaborator]["extra_hours"]   += r.extra_hours or 0.0
        per_collab[r.collaborator]["standby_hours"] += r.standby_hours or 0.0

    chart_data = [
        {"collaborator": name, **hours}
        for name, hours in sorted(
            per_collab.items(),
            key=lambda x: -(x[1]["normal_hours"] + x[1]["extra_hours"] + x[1]["standby_hours"])
        )
    ]

    budget_vs_actual = _compute_budget_vs_actual(db, pep_code, None, collaborator_id)
    return {
        "cycle": {"id": None, "name": "Toda a base", "start_date": None, "end_date": None, "is_quarantine": False},
        "filters": {"pep_codes": pep_code, "pep_descriptions": pep_description, "collaborator_ids": collaborator_id},
        "data": chart_data,
        "breakdown": [],
        "budget_vs_actual": budget_vs_actual,
    }


@app.get("/api/dashboard/{cycle_id}", summary="Dashboard de horas por ciclo")
def get_dashboard(
    cycle_id: int,
    db: DbSession,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
):
    cycle = db.get(Cycle, cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado.")

    q = (
        db.query(
            Collaborator.id.label("collaborator_id"),
            Collaborator.name.label("collaborator"),
            TimesheetRecord.pep_wbs,
            TimesheetRecord.pep_description,
            func.sum(TimesheetRecord.normal_hours).label("normal_hours"),
            func.sum(TimesheetRecord.extra_hours).label("extra_hours"),
            func.sum(TimesheetRecord.standby_hours).label("standby_hours"),
        )
        .join(Collaborator, TimesheetRecord.collaborator_id == Collaborator.id)
        .filter(TimesheetRecord.cycle_id == cycle_id)
    )

    if pep_code:
        q = q.filter(TimesheetRecord.pep_wbs.in_(pep_code))
    if pep_description:
        q = q.filter(TimesheetRecord.pep_description.in_(pep_description))
    if collaborator_id:
        q = q.filter(TimesheetRecord.collaborator_id.in_(collaborator_id))

    group_by_pep = not pep_description
    if group_by_pep:
        rows = (
            q.group_by(TimesheetRecord.collaborator_id, TimesheetRecord.pep_description)
            .order_by(Collaborator.name, TimesheetRecord.pep_description)
            .all()
        )
    else:
        rows = (
            q.group_by(TimesheetRecord.collaborator_id)
            .order_by(Collaborator.name)
            .all()
        )

    from collections import defaultdict
    per_collab: dict[str, dict] = defaultdict(
        lambda: {"normal_hours": 0.0, "extra_hours": 0.0, "standby_hours": 0.0}
    )
    breakdown = []
    for r in rows:
        per_collab[r.collaborator]["normal_hours"]  += r.normal_hours or 0.0
        per_collab[r.collaborator]["extra_hours"]   += r.extra_hours or 0.0
        per_collab[r.collaborator]["standby_hours"] += r.standby_hours or 0.0
        breakdown.append({
            "collaborator": r.collaborator,
            "pep_code": r.pep_wbs,
            "pep_description": r.pep_description,
            "normal_hours": r.normal_hours or 0.0,
            "extra_hours": r.extra_hours or 0.0,
            "standby_hours": r.standby_hours or 0.0,
        })

    chart_data = [
        {"collaborator": name, **hours}
        for name, hours in sorted(
            per_collab.items(),
            key=lambda x: -(x[1]["normal_hours"] + x[1]["extra_hours"] + x[1]["standby_hours"])
        )
    ]

    budget_vs_actual = _compute_budget_vs_actual(db, pep_code, cycle_id, collaborator_id)
    return {
        "cycle": {
            "id": cycle.id,
            "name": cycle.name,
            "start_date": cycle.start_date.isoformat(),
            "end_date": cycle.end_date.isoformat(),
            "is_quarantine": cycle.is_quarantine,
        },
        "filters": {
            "pep_codes": pep_code,
            "pep_descriptions": pep_description,
            "collaborator_ids": collaborator_id,
        },
        "data": chart_data,
        "breakdown": breakdown,
        "budget_vs_actual": budget_vs_actual,
    }
