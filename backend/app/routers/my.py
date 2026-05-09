from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import QuarantineRecord, UploadSession, UserPreference
from backend.app.schemas import (
    AlertSummaryOut,
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
    pref.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pref)
    return pref


# ── Upload history ────────────────────────────────────────────────────────────

@router.get("/upload-history", response_model=list[UploadSessionOut])
def my_upload_history(db: DbSession, current_user: CurrentUser, limit: int = 200, offset: int = 0):
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
    limit: int = 200,
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
                rd.get("collaborator"), rd.get("date"), rd.get("hours"),
                rd.get("pep_code"), rd.get("pep_desc"),
                rd.get("extra_hours"), rd.get("standby_hours"),
                rec.quarantine_reason, rec.rule_id,
                rec.reviewed, rec.reviewed_by, rec.reviewed_at,
            ])
            yield buf.getvalue()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    filename = f"quarantine_{current_user.username}_{today}.csv"
    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=list[AlertSummaryOut])
def my_alerts(db: DbSession, current_user: CurrentUser):
    q = db.query(UploadSession).order_by(UploadSession.uploaded_at.desc()).limit(50)
    if current_user.role != "admin":
        q = q.filter(UploadSession.uploaded_by_user_id == current_user.id)
    sessions = q.all()

    # Aggregate: message → list of (uploaded_at) sorted newest first
    occurrences: dict[str, list[datetime]] = defaultdict(list)
    for s in sessions:
        for msg in (s.warnings_detail or []) + (s.infos_detail or []):
            occurrences[msg].append(s.uploaded_at)

    result = []
    for msg, times in occurrences.items():
        times_sorted = sorted(times, reverse=True)
        last3 = [len([t for t in times if t <= sessions[i].uploaded_at]) for i in range(min(3, len(sessions)))]
        # Simple trend: compare first half vs second half of last 6 occurrences
        if len(times_sorted) >= 4:
            recent = len([t for t in times_sorted[:3]])
            older = len([t for t in times_sorted[3:6]])
            trend = "up" if recent > older else ("down" if recent < older else "stable")
        else:
            trend = "stable"
        result.append(AlertSummaryOut(
            message=msg,
            occurrences=len(times_sorted),
            last_triggered=times_sorted[0],
            trend=trend,
        ))

    result.sort(key=lambda a: a.last_triggered, reverse=True)
    return result
