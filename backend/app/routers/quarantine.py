from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import QuarantineRecord, UploadSession
from backend.app.schemas import QuarantineRecordOut, QuarantineReviewIn

router = APIRouter(
    prefix="/api/quarantine",
    tags=["quarantine"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[QuarantineRecordOut])
def list_quarantine(
    db: DbSession,
    _: AdminUser,
    reviewed: bool | None = None,
    upload_session_id: int | None = None,
    rule_id: int | None = None,
    source_file: str | None = None,
    username: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    q = db.query(QuarantineRecord).order_by(QuarantineRecord.ingested_at.desc())
    if reviewed is not None:
        q = q.filter(QuarantineRecord.reviewed == reviewed)
    if upload_session_id is not None:
        q = q.filter(QuarantineRecord.upload_session_id == upload_session_id)
    if rule_id is not None:
        q = q.filter(QuarantineRecord.rule_id == rule_id)
    if source_file is not None:
        q = q.join(UploadSession, QuarantineRecord.upload_session_id == UploadSession.id).filter(
            UploadSession.source_file.ilike(f"%{source_file}%")
        )
    if username is not None:
        q = q.filter(QuarantineRecord.uploaded_by_username == username)
    return q.offset(offset).limit(limit).all()


@router.patch("/{record_id}/review", response_model=QuarantineRecordOut)
def review_quarantine(
    record_id: int,
    payload: QuarantineReviewIn,
    db: DbSession,
    current_user: AdminUser,
):
    rec = db.get(QuarantineRecord, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    rec.reviewed = payload.reviewed
    rec.reviewed_by = current_user.username
    rec.reviewed_at = datetime.utcnow() if payload.reviewed else None
    db.commit()
    db.refresh(rec)
    log_audit(db, current_user, "review", "quarantine_record", record_id, {"reviewed": payload.reviewed})
    db.commit()
    return rec


@router.delete("/{record_id}", status_code=204)
def delete_quarantine_record(record_id: int, db: DbSession, current_user: AdminUser):
    rec = db.get(QuarantineRecord, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    log_audit(db, current_user, "delete", "quarantine_record", record_id, {})
    db.delete(rec)
    db.commit()
