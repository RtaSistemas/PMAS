from __future__ import annotations

import logging
import os
import sys
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db, init_db
from backend.app.models import Collaborator, Cycle, TimesheetRecord
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
# Reference data
# ---------------------------------------------------------------------------

@app.get("/api/cycles", summary="Listar ciclos")
def list_cycles(db: DbSession):
    cycles = db.query(Cycle).order_by(Cycle.start_date).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "start_date": c.start_date.isoformat(),
            "end_date": c.end_date.isoformat(),
            "is_quarantine": c.is_quarantine,
        }
        for c in cycles
    ]


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
# Dashboard (with filters)
# ---------------------------------------------------------------------------

@app.get("/api/dashboard", summary="Dashboard sem filtro de ciclo — toda a base")
def get_dashboard_all(
    db: DbSession,
    pep_code: List[str] = Query(default=[]),
    pep_description: List[str] = Query(default=[]),
    collaborator_id: List[int] = Query(default=[]),
):
    """Agrega horas de todos os ciclos, com filtros opcionais de PEP e colaborador."""
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

    return {
        "cycle": {
            "id":            None,
            "name":          "Toda a base",
            "start_date":    None,
            "end_date":      None,
            "is_quarantine": False,
        },
        "filters": {
            "pep_codes":        pep_code,
            "pep_descriptions": pep_description,
            "collaborator_ids": collaborator_id,
        },
        "data":      chart_data,
        "breakdown": [],
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
        per_collab[r.collaborator]["normal_hours"] += r.normal_hours or 0.0
        per_collab[r.collaborator]["extra_hours"]  += r.extra_hours or 0.0
        per_collab[r.collaborator]["standby_hours"] += r.standby_hours or 0.0
        breakdown.append({
            "collaborator":    r.collaborator,
            "pep_code":        r.pep_wbs,
            "pep_description": r.pep_description,
            "normal_hours":    r.normal_hours or 0.0,
            "extra_hours":     r.extra_hours or 0.0,
            "standby_hours":   r.standby_hours or 0.0,
        })

    chart_data = [
        {"collaborator": name, **hours}
        for name, hours in sorted(
            per_collab.items(),
            key=lambda x: -(x[1]["normal_hours"] + x[1]["extra_hours"] + x[1]["standby_hours"])
        )
    ]

    return {
        "cycle": {
            "id":           cycle.id,
            "name":         cycle.name,
            "start_date":   cycle.start_date.isoformat(),
            "end_date":     cycle.end_date.isoformat(),
            "is_quarantine": cycle.is_quarantine,
        },
        "filters": {
            "pep_codes":        pep_code,
            "pep_descriptions": pep_description,
            "collaborator_ids": collaborator_id,
        },
        "data":      chart_data,
        "breakdown": breakdown,
    }
