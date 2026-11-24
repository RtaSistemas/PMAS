from __future__ import annotations

import logging
import logging.config
import logging.handlers
import math
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.database import DbSession, init_db
from backend.app.limiter import limiter
from backend.app.routers import (
    acl, api_keys, auditlog, auth, baselines, cycles, dashboard,
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
    version="2.1.0",
    lifespan=_lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── Error handlers ────────────────────────────────────────────────────────────

_PT_MESSAGES: dict[str, str] = {
    "missing": "campo obrigatório",
    "string_too_short": "texto curto demais (mínimo de {min_length} caracteres)",
    "string_too_long": "texto longo demais (máximo de {max_length} caracteres)",
    "string_type": "deve ser um texto",
    "int_type": "deve ser um número inteiro",
    "int_parsing": "deve ser um número inteiro válido",
    "int_from_float": "deve ser um número inteiro",
    "float_type": "deve ser um número",
    "float_parsing": "deve ser um número válido",
    "bool_type": "deve ser verdadeiro ou falso",
    "bool_parsing": "deve ser verdadeiro ou falso",
    "date_type": "deve ser uma data",
    "date_parsing": "data inválida (use AAAA-MM-DD)",
    "date_from_datetime_parsing": "data inválida (use AAAA-MM-DD)",
    "datetime_parsing": "data/hora inválida",
    "greater_than": "deve ser maior que {gt}",
    "greater_than_equal": "deve ser maior ou igual a {ge}",
    "less_than": "deve ser menor que {lt}",
    "less_than_equal": "deve ser menor ou igual a {le}",
    "finite_number": "deve ser um número finito",
    "literal_error": "valor não permitido (permitidos: {expected})",
    "enum": "valor não permitido (permitidos: {expected})",
    "dict_type": "deve ser um objeto",
    "list_type": "deve ser uma lista",
    "json_invalid": "JSON inválido",
    "model_attributes_type": "deve ser um objeto",
    "missing_argument": "campo obrigatório",
}


class _SafeFormat(dict):
    def __missing__(self, key):
        return "?"


def _translate_validation_error(err: dict) -> str:
    """Portuguese message for one pydantic error; falls back to the original text."""
    etype = err.get("type", "")
    original = str(err.get("msg", "") or "")
    ctx = err.get("ctx") or {}
    if etype == "value_error":
        # Custom validators already raise Portuguese text; drop pydantic's prefix.
        text = original
        if text.lower().startswith("value error, "):
            text = text[len("Value error, "):]
        return text or "valor inválido"
    template = _PT_MESSAGES.get(etype)
    if template is None:
        return original or "valor inválido"
    try:
        return template.format_map(_SafeFormat(dict(ctx)))
    except Exception:
        return original or "valor inválido"


def _loc_to_field(loc) -> str:
    skip = ("body", "query", "path", "header", "cookie")
    return ".".join(str(p) for p in (loc or ()) if p not in skip)


def _json_safe(value):
    """NaN / Infinity are not valid JSON: send them back as text."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _safe_error(err: dict) -> dict:
    """JSON-safe copy of a pydantic error (bytes / exception objects in input / ctx)."""
    out: dict = {}
    for key in ("type", "loc", "input", "ctx"):
        if key not in err:
            continue
        try:
            out[key] = _json_safe(jsonable_encoder(
                err[key],
                custom_encoder={bytes: lambda b: b.decode("utf-8", "replace"), Exception: str},
            ))
        except Exception:
            out[key] = str(err[key])
    out["msg"] = _translate_validation_error(err)
    return out


async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    parts: list[str] = []
    for err in errors:
        field = _loc_to_field(err.get("loc"))
        msg = _translate_validation_error(err)
        parts.append(f"Campo '{field}': {msg}" if field else msg)
    detail = "; ".join(parts) if parts else "Requisição inválida."
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "errors": [_safe_error(e) for e in errors]},
    )


async def _unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Erro interno do servidor",
            "status": 500,
            "detail": "Ocorreu um erro inesperado. Tente novamente; se persistir, contate o administrador.",
            "instance": request.url.path,
        },
    )


async def _overflow_handler(request: Request, exc: OverflowError):
    # An id larger than SQLite's 64-bit integer cannot exist: treat as not found.
    return JSONResponse(status_code=404, content={"detail": "Registro não encontrado."})


app.add_exception_handler(OverflowError, _overflow_handler)
app.add_exception_handler(RequestValidationError, _validation_exception_handler)
app.add_exception_handler(Exception, _unhandled_exception_handler)

# ── Rate limiting ─────────────────────────────────────────────────────────────

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── RFC 7807 Problem Details error responses ──────────────────────────────────

def _problem(status: int, title: str, detail: str, headers: dict | None = None, **extra) -> JSONResponse:
    body = {"type": "about:blank", "title": title, "status": status, "detail": detail}
    body.update(extra)
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
        headers=headers,
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    titles = {
        400: "Requisição inválida",
        401: "Não autenticado",
        403: "Sem permissão",
        404: "Não encontrado",
        409: "Conflito",
        422: "Dados inválidos",
        429: "Muitas requisições",
        500: "Erro interno",
        503: "Serviço indisponível",
    }
    title = titles.get(exc.status_code, "Erro")
    return _problem(exc.status_code, title, str(exc.detail), headers=getattr(exc, "headers", None))


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
app.include_router(api_keys.router)
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
