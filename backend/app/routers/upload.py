from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile

from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.limiter import limiter
from backend.app.models import UploadSession
from backend.app.schemas import UploadOut, UploadSessionOut
from backend.app.services.ingestion import (
    ArchivedCycleError,
    ClosedCycleError,
    LockedProjectError,
    ingest_file,
)
from backend.app.services.notifications_svc import (
    create_notification,
    notify_schedule_risk,
    notify_threshold_crossings,
)
from backend.app.services.upload_session_svc import create_upload_session

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["upload"],
    dependencies=[Depends(get_current_user)],
)

_MAX_UPLOAD_MB = int(os.getenv("PMAS_MAX_UPLOAD_MB", "20"))
_MAX_UPLOAD_BYTES = _MAX_UPLOAD_MB * 1024 * 1024


def _save_rejected_session(db, user, fname: str, reason: str) -> None:
    try:
        create_upload_session(
            db, user_id=user.id, username=user.username,
            source_file=fname, status="rejected",
            inserted=0, skipped=0, quarantine=0,
            warning_count=1, info_count=0, warnings=[reason], infos=[],
        )
        db.commit()
    except Exception:
        db.rollback()


@router.post("/upload-timesheet", summary="Ingerir CSV ou XLSX de timesheet", response_model=UploadOut)
@limiter.limit(os.getenv("PMAS_UPLOAD_RATE_LIMIT", "60/minute"))
def upload_timesheet(request: Request, file: UploadFile, db: DbSession, current_user: CurrentUser):
    fname = Path(file.filename or "").name or "upload"
    if not any(fname.lower().endswith(ext) for ext in (".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv ou .xlsx são aceitos.")
    contents = file.file.read(_MAX_UPLOAD_BYTES + 1)
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {_MAX_UPLOAD_MB} MB.",
        )
    try:
        summary = ingest_file(
            contents, fname, db,
            user_role=current_user.role,
            user_id=current_user.id,
            username=current_user.username,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except (ClosedCycleError, ArchivedCycleError) as exc:
        db.rollback()
        _save_rejected_session(db, current_user, fname, str(exc))
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LockedProjectError as exc:
        db.rollback()
        _save_rejected_session(db, current_user, fname, str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        _save_rejected_session(db, current_user, fname, str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        _save_rejected_session(db, current_user, fname, "Erro interno durante ingestão.")
        log.exception("Erro inesperado durante ingestão.")
        raise HTTPException(status_code=500, detail="Erro interno durante ingestão.") from exc



    accepted = summary.get("records_inserted", 0)
    quarantined = summary.get("quarantine_records_added", 0)
    level = "info" if quarantined == 0 else "warning"
    message = (
        f"Upload '{fname}' processado: {accepted} registros aceitos, "
        f"{quarantined} em quarentena."
    )
    create_notification(db, current_user.id, message, level=level)

    notify_threshold_crossings(db, summary.get("affected_peps", []))
    notify_schedule_risk(db, summary.get("affected_peps", []))

    db.commit()

    return summary


@router.get("/summaries/status", summary="Estado de sincronização das summaries analíticas")
def summaries_status(db: DbSession, _current_user: AdminUser):
    """Returns whether PepCycleSummary is up-to-date with the latest upload."""
    from backend.app.models import PepCycleSummary, CollaboratorCycleSummary
    from sqlalchemy import func

    latest_upload = db.query(func.max(UploadSession.uploaded_at)).scalar()
    oldest_pep_refresh = db.query(func.min(PepCycleSummary.refreshed_at)).scalar()
    oldest_collab_refresh = db.query(func.min(CollaboratorCycleSummary.refreshed_at)).scalar()

    if latest_upload is None:
        return {"stale": False, "reason": None}

    stale_pep = oldest_pep_refresh is None or oldest_pep_refresh < latest_upload
    stale_collab = oldest_collab_refresh is None or oldest_collab_refresh < latest_upload
    stale = stale_pep or stale_collab

    return {
        "stale": stale,
        "latest_upload_at": latest_upload.isoformat() if latest_upload else None,
        "oldest_pep_refresh_at": oldest_pep_refresh.isoformat() if oldest_pep_refresh else None,
        "oldest_collab_refresh_at": oldest_collab_refresh.isoformat() if oldest_collab_refresh else None,
        "reason": "Summaries mais antigas que o último upload" if stale else None,
    }


@router.get("/upload-history", response_model=list[UploadSessionOut])
def list_upload_sessions(db: DbSession, current_user: CurrentUser, limit: int = Query(default=200, le=1000), offset: int = 0):
    q = db.query(UploadSession).order_by(UploadSession.uploaded_at.desc())
    if current_user.role != "admin":
        q = q.filter(UploadSession.uploaded_by_user_id == current_user.id)
    return q.offset(offset).limit(limit).all()


@router.get("/upload-history/{session_id}", response_model=UploadSessionOut)
def get_upload_session(session_id: int, db: DbSession, current_user: CurrentUser):
    session = db.get(UploadSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if current_user.role != "admin" and session.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    return session
