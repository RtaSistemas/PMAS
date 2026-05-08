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

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["upload"],
    dependencies=[Depends(get_current_user)],
)

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


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
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LockedProjectError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Erro inesperado durante ingestão.")
        raise HTTPException(status_code=500, detail="Erro interno durante ingestão.") from exc
    return summary


@router.get("/upload-history", response_model=list[UploadSessionOut])
def list_upload_sessions(db: DbSession, _: AdminUser, limit: int = 200, offset: int = 0):
    return (
        db.query(UploadSession)
        .order_by(UploadSession.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/upload-history/{session_id}", response_model=UploadSessionOut)
def get_upload_session(session_id: int, db: DbSession, _: AdminUser):
    session = db.get(UploadSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return session
