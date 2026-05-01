from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.database import DbSession, init_db
from backend.app.deps import CurrentUser
from backend.app.schemas import UploadOut
from backend.app.routers import analytics, auth, cycles, dashboard, projects, ratecard, reference, users
from backend.app.services.ingestion import ClosedCycleError, LockedProjectError, ingest_file

log = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    log.info("PMAS API pronta. Banco inicializado.")
    yield


app = FastAPI(
    title="PMAS API",
    description="Project Management Assistant System — Timesheet Foundation",
    version="1.0.0",
    lifespan=_lifespan,
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(users.router)
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


_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@app.post("/api/upload-timesheet", summary="Ingerir CSV ou XLSX de timesheet", response_model=UploadOut)
def upload_timesheet(file: UploadFile, db: DbSession, current_user: CurrentUser):
    fname = file.filename or ""
    if not any(fname.lower().endswith(ext) for ext in (".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv ou .xlsx são aceitos.")
    contents = file.file.read(_MAX_UPLOAD_BYTES + 1)
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 20 MB.")
    try:
        summary = ingest_file(contents, fname, db, user_role=current_user.role)
    except ClosedCycleError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LockedProjectError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Erro inesperado durante ingestão.")
        raise HTTPException(status_code=500, detail="Erro interno durante ingestão.") from exc
    return {"status": "ok", **summary}
