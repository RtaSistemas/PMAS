from __future__ import annotations

import logging
import logging.config
import logging.handlers
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.database import DbSession, init_db
from backend.app.limiter import limiter
from backend.app.routers import (
    acl, auditlog, auth, baselines, cycles, dashboard,
    my, notifications, plans, project_alerts, projects, quarantine, ratecard,
    theme, upload, users, validation_rules,
)
from backend.app.routers.v2 import (
    allocation as allocation_v2,
    concentration as concentration_v2,
    effort, filters, forecast, monte_carlo as monte_carlo_v2,
    over_allocation as over_allocation_v2,
    portfolio,
    runway as runway_v2,
    simulate as simulate_v2,
    trends as trends_v2,
)

# ── Logging ───────────────────────────────────────────────────────────────────

_LOG_LEVEL = os.getenv("PMAS_LOG_LEVEL", "INFO").upper()
_LOG_FILE  = os.getenv("PMAS_LOG_FILE", "")   # empty = console only

_handlers: list[str] = ["console"]
_handler_cfg: dict = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "standard",
    },
}
if _LOG_FILE:
    _handler_cfg["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "standard",
        "filename": _LOG_FILE,
        "maxBytes": 10 * 1024 * 1024,   # 10 MB per file
        "backupCount": 5,
        "encoding": "utf-8",
    }
    _handlers.append("file")

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": _handler_cfg,
    "root": {"level": _LOG_LEVEL, "handlers": _handlers},
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
    version="2.0.2",
    lifespan=_lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── Rate limiting ─────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Security headers ──────────────────────────────────────────────────────────

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)


@app.middleware("http")
async def _security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = _CSP
    return response


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
app.include_router(notifications.router)
app.include_router(project_alerts.router)
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
app.include_router(simulate_v2.router)
app.include_router(monte_carlo_v2.router)


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


@app.get("/health", tags=["ops"])
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
    }


@app.get("/ready", tags=["ops"])
def ready(db: DbSession):
    from sqlalchemy import text as _text
    try:
        db.execute(_text("SELECT 1"))
    except Exception:
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(status_code=503, detail="Database unavailable.")
    return {"status": "ready"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/frontend/index.html")
