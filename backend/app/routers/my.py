from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import QuarantineRecord, UploadSession, UserPreference
from backend.app.schemas import (
    QuarantineRecordOut,
    UploadSessionOut,
    UserPreferenceIn,
    UserPreferenceOut,
)

router = APIRouter(
    prefix="/api/my",
    tags=["my"],
    dependencies=[Depends(get_current_user)],
)


# ── Preferences ──────────────────────────────────────────────────────────────

@router.get("/preferences", response_model=UserPreferenceOut)
def get_preferences(db: DbSession, current_user: CurrentUser):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if pref is None:
        return UserPreferenceOut(user_id=current_user.id, dashboard=None, updated_at=None)
    return pref


@router.put("/preferences", response_model=UserPreferenceOut)
def save_preferences(payload: UserPreferenceIn, db: DbSession, current_user: CurrentUser):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if pref is None:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
    pref.dashboard = payload.dashboard
    pref.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pref)
    return pref


# ── Upload history ────────────────────────────────────────────────────────────

@router.get("/upload-history", response_model=list[UploadSessionOut])
def my_upload_history(db: DbSession, current_user: CurrentUser, limit: int = Query(default=200, le=1000), offset: int = 0):
    q = db.query(UploadSession).order_by(UploadSession.uploaded_at.desc())
    if current_user.role != "admin":
        q = q.filter(UploadSession.uploaded_by_user_id == current_user.id)
    return q.offset(offset).limit(limit).all()


@router.get("/upload-history/{session_id}", response_model=UploadSessionOut)
def my_upload_history_detail(session_id: int, db: DbSession, current_user: CurrentUser):
    session = db.get(UploadSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    if current_user.role != "admin" and session.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado.")
    return session


# ── Quarantine ────────────────────────────────────────────────────────────────

@router.get("/quarantine", response_model=list[QuarantineRecordOut])
def my_quarantine(
    db: DbSession,
    current_user: CurrentUser,
    reviewed: bool | None = None,
    source_file: str | None = None,
    limit: int = Query(default=200, le=1000),
    offset: int = 0,
):
    q = db.query(QuarantineRecord).order_by(QuarantineRecord.ingested_at.desc())
    if current_user.role != "admin":
        q = q.filter(QuarantineRecord.uploaded_by_user_id == current_user.id)
    if reviewed is not None:
        q = q.filter(QuarantineRecord.reviewed == reviewed)
    if source_file is not None:
        q = q.join(UploadSession, QuarantineRecord.upload_session_id == UploadSession.id).filter(
            UploadSession.source_file.ilike(f"%{source_file}%")
        )
    return q.offset(offset).limit(limit).all()


@router.get("/quarantine/export")
def export_quarantine_csv(db: DbSession, current_user: CurrentUser):
    q = db.query(QuarantineRecord).order_by(QuarantineRecord.ingested_at)
    if current_user.role != "admin":
        q = q.filter(QuarantineRecord.uploaded_by_user_id == current_user.id)

    def _generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "id", "ingested_at", "upload_session_id", "uploaded_by_username",
            "collaborator", "date", "hours", "pep_code", "pep_desc",
            "extra_hours", "standby_hours",
            "quarantine_reason", "rule_id", "reviewed", "reviewed_by", "reviewed_at",
        ])
        yield buf.getvalue()
        for rec in q:
            buf = io.StringIO()
            writer = csv.writer(buf)
            rd = rec.raw_data or {}
            writer.writerow([
                rec.id, rec.ingested_at, rec.upload_session_id, rec.uploaded_by_username,
                rd.get("Colaborador"), rd.get("Data"), rd.get("Horas totais (decimal)"),
                rd.get("Código PEP"), rd.get("PEP"),
                rd.get("Hora extra"), rd.get("Hora sobreaviso"),
                rec.quarantine_reason, rec.rule_id,
                rec.reviewed, rec.reviewed_by, rec.reviewed_at,
            ])
            yield buf.getvalue()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"quarantine_{current_user.username}_{today}.csv"
    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
