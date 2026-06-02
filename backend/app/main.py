from __future__ import annotations

import logging
import logging.config
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.database import init_db
from backend.app.limiter import limiter
from backend.app.routers import (
    acl, auditlog, auth, baselines, cycles, dashboard,
    my, plans, projects, quarantine, ratecard,
    theme, upload, users, validation_rules,
)
from backend.app.routers.v2 import (
    allocation as allocation_v2,
    concentration as concentration_v2,
    effort, filters, forecast, portfolio,
    over_allocation as over_allocation_v2,
    runway as runway_v2,
    trends as trends_v2,
)

# ── Logging ───────────────────────────────────────────────────────────────────

_LOG_LEVEL = os.getenv("PMAS_LOG_LEVEL", "INFO").upper()

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {"level": _LOG_LEVEL, "handlers": ["console"]},
    "loggers": {
        "sqlalchemy.engine": {"level": "WARNING", "propagate": True},
        "uvicorn":           {"propagate": True},
        "uvicorn.error":     {"propagate": True},
        "uvicorn.access":    {"propagate": True},
    },
})

log = logging.getLogger(__name__)


# ── App ───────────────────────────────────────────────────────────────────────

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

# ── Rate limiting ─────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────

_port = os.getenv("PMAS_PORT", "8765")
_extra_origins = [o.strip() for o in os.getenv("PMAS_ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        f"http://localhost:{_port}",
        "http://127.0.0.1",
        f"http://127.0.0.1:{_port}",
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(auditlog.router)
app.include_router(cycles.router)
app.include_router(projects.router)
app.include_router(plans.router)
app.include_router(baselines.router)
app.include_router(dashboard.router)
app.include_router(ratecard.router)
app.include_router(acl.router)
app.include_router(upload.router)
app.include_router(quarantine.router)
app.include_router(validation_rules.router)
app.include_router(my.router)
app.include_router(theme.router)
# v2 endpoints — consolidated, render-ready, ACL-enforced
app.include_router(filters.router)
app.include_router(portfolio.router)
app.include_router(effort.router)
app.include_router(trends_v2.router)
app.include_router(forecast.router)
app.include_router(allocation_v2.router)
app.include_router(runway_v2.router)
app.include_router(concentration_v2.router)
app.include_router(over_allocation_v2.router)


def _frontend_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "frontend")
    return os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


def _static_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "static")
    return os.path.join(os.path.dirname(__file__), "..", "..", "static")


_static_path = _static_dir()
if os.path.isdir(_static_path):
    app.mount("/static", StaticFiles(directory=_static_path), name="static_assets")

app.mount("/frontend", StaticFiles(directory=_frontend_dir(), html=True), name="frontend")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/frontend/index.html")
