from __future__ import annotations

import logging
import os
import sys
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.app.database import get_db, init_db
from backend.app.routers import analytics, cycles, dashboard, projects, ratecard, reference
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

app.include_router(cycles.router)
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(reference.router)
app.include_router(analytics.router)
app.include_router(ratecard.router)


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
