from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import QuarantineRecord
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
    limit: int = 200,
    offset: int = 0,
):
    q = db.query(QuarantineRecord).order_by(QuarantineRecord.ingested_at.desc())
    if reviewed is not None:
        q = q.filter(QuarantineRecord.reviewed == reviewed)
    if upload_session_id is not None:
        q = q.filter(QuarantineRecord.upload_session_id == upload_session_id)
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
    return rec
