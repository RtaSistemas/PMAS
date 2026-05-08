from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app.database import init_db
from backend.app.routers import (
    acl, analytics, auditlog, auth, cycles, dashboard,
    my, plans, projects, quarantine, ratecard, reference,
    theme, upload, users, validation_rules,
)

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
app.include_router(auditlog.router)
app.include_router(cycles.router)
app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(dashboard.router)
app.include_router(reference.router)
app.include_router(analytics.router)
app.include_router(ratecard.router)
app.include_router(acl.router)
app.include_router(upload.router)
app.include_router(quarantine.router)
app.include_router(validation_rules.router)
app.include_router(my.router)
app.include_router(theme.router)


def _frontend_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "frontend")
    return os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


app.mount("/frontend", StaticFiles(directory=_frontend_dir(), html=True), name="frontend")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/frontend/index.html")
