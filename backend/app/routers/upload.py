from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import UploadSession
from backend.app.schemas import UploadOut, UploadSessionOut
from backend.app.services.ingestion import (
    ArchivedCycleError,
    ClosedCycleError,
    LockedProjectError,
    ingest_file,
)
from backend.app.services.upload_session_svc import create_upload_session

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["upload"],
    dependencies=[Depends(get_current_user)],
)

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


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
def upload_timesheet(file: UploadFile, db: DbSession, current_user: CurrentUser):
    fname = file.filename or ""
    if not any(fname.lower().endswith(ext) for ext in (".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv ou .xlsx são aceitos.")
    contents = file.file.read(_MAX_UPLOAD_BYTES + 1)
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 20 MB.")
    try:
        summary = ingest_file(
            contents, fname, db,
            user_role=current_user.role,
            user_id=current_user.id,
            username=current_user.username,
        )
        log_audit(db, current_user, "import", "timesheet", detail={
            "file": fname,
            "status": summary["status"],
            "records_inserted": summary["records_inserted"],
            "records_skipped": summary["records_skipped"],
            "quarantine_records_added": summary.get("quarantine_records_added", 0),
        })
        db.commit()
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
    return summary


@router.get("/upload-history", response_model=list[UploadSessionOut])
def list_upload_sessions(db: DbSession, current_user: CurrentUser, limit: int = 200, offset: int = 0):
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
