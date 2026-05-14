from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import Collaborator, QuarantineRecord, TimesheetRecord, UploadSession
from backend.app.schemas import QuarantineRecordOut, QuarantineReviewIn
from backend.app.services.ingestion import (
    ArchivedCycleError,
    _COL_COLLABORATOR,
    _COL_DATE,
    _COL_EXTRA,
    _COL_HOURS,
    _COL_PEP_CODE,
    _COL_PEP_DESC,
    _COL_STANDBY,
    _get_or_create_collaborator,
    _is_yes,
    _lookup_rate,
    _parse_date_safe,
    _resolve_cycle,
    _safe_hours,
    _str_or_none,
)

router = APIRouter(
    prefix="/api/quarantine",
    tags=["quarantine"],
    dependencies=[Depends(get_current_user)],
)


def _load_qr(db: Session, record_id: int) -> QuarantineRecord:
    rec = (
        db.query(QuarantineRecord)
        .options(joinedload(QuarantineRecord.rule))
        .filter(QuarantineRecord.id == record_id)
        .first()
    )
    if rec is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    return rec


def _ingest_from_raw(db: Session, rec: QuarantineRecord) -> None:
    """Insert a TimesheetRecord from quarantine raw_data, bypassing validation rules."""
    raw = rec.raw_data or {}

    name = _str_or_none(raw.get(_COL_COLLABORATOR))
    if not name:
        raise ValueError("Nome de colaborador ausente nos dados brutos.")

    record_date = _parse_date_safe(raw.get(_COL_DATE))
    if record_date is None:
        raise ValueError(f"Data inválida nos dados brutos: {raw.get(_COL_DATE)!r}")

    total_h = _safe_hours(raw.get(_COL_HOURS))
    if total_h is None or total_h == 0.0:
        raise ValueError(f"Horas inválidas nos dados brutos: {raw.get(_COL_HOURS)!r}")

    try:
        cycle = _resolve_cycle(db, record_date)
    except ArchivedCycleError:
        raise ValueError(
            f"Nenhum ciclo ativo encontrado para a data {record_date}. "
            "Crie ou ative um ciclo antes de aprovar este registro."
        )

    collab, _ = _get_or_create_collaborator(db, name)
    pep_code = _str_or_none(raw.get(_COL_PEP_CODE))
    pep_desc = _str_or_none(raw.get(_COL_PEP_DESC))
    is_extra   = _is_yes(raw.get(_COL_EXTRA, ""))
    is_standby = _is_yes(raw.get(_COL_STANDBY, ""))

    if is_extra:
        normal_h, extra_h, standby_h = 0.0, total_h, 0.0
    elif is_standby:
        normal_h, extra_h, standby_h = 0.0, 0.0, total_h
    else:
        normal_h, extra_h, standby_h = total_h, 0.0, 0.0

    rate = _lookup_rate(db, collab, record_date)
    db.add(TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=record_date,
        pep_wbs=pep_code,
        pep_description=pep_desc,
        normal_hours=normal_h,
        extra_hours=extra_h,
        standby_hours=standby_h,
        cost_per_hour=rate,
    ))
    db.flush()


@router.get("", response_model=list[QuarantineRecordOut])
def list_quarantine(
    db: DbSession,
    current_user: CurrentUser,
    reviewed: bool | None = None,
    review_status: str | None = None,
    upload_session_id: int | None = None,
    rule_id: int | None = None,
    source_file: str | None = None,
    username: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    q = (
        db.query(QuarantineRecord)
        .options(joinedload(QuarantineRecord.rule))
        .order_by(QuarantineRecord.ingested_at.desc())
    )
    if current_user.role != "admin":
        q = q.filter(QuarantineRecord.uploaded_by_user_id == current_user.id)
    if reviewed is not None:
        q = q.filter(QuarantineRecord.reviewed == reviewed)
    if review_status is not None:
        q = q.filter(QuarantineRecord.review_status == review_status)
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


@router.get("/{record_id}", response_model=QuarantineRecordOut)
def get_quarantine_record(record_id: int, db: DbSession, current_user: CurrentUser):
    rec = _load_qr(db, record_id)
    if current_user.role != "admin" and rec.uploaded_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    return rec


@router.patch("/{record_id}/review", response_model=QuarantineRecordOut)
def review_quarantine(
    record_id: int,
    payload: QuarantineReviewIn,
    db: DbSession,
    current_user: AdminUser,
):
    rec = _load_qr(db, record_id)
    rec.reviewed = payload.reviewed
    rec.reviewed_by = current_user.username
    rec.reviewed_at = datetime.now(timezone.utc) if payload.reviewed else None
    log_audit(db, current_user, "review", "quarantine_record", record_id, {"reviewed": payload.reviewed})
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/{record_id}/approve", response_model=QuarantineRecordOut)
def approve_quarantine(record_id: int, db: DbSession, current_user: AdminUser):
    rec = _load_qr(db, record_id)
    if rec.review_status == "approved":
        raise HTTPException(status_code=409, detail="Registro já aprovado.")

    try:
        _ingest_from_raw(db, rec)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    rec.review_status = "approved"
    rec.reviewed = True
    rec.reviewed_by = current_user.username
    rec.reviewed_at = datetime.now(timezone.utc)
    log_audit(db, current_user, "approve", "quarantine_record", record_id, {})
    db.commit()
    db.refresh(rec)
    return rec


@router.post("/{record_id}/reject", response_model=QuarantineRecordOut)
def reject_quarantine(record_id: int, db: DbSession, current_user: AdminUser):
    rec = _load_qr(db, record_id)
    if rec.review_status == "approved":
        raise HTTPException(status_code=409, detail="Registro já aprovado — não pode ser rejeitado.")

    rec.review_status = "rejected"
    rec.reviewed = True
    rec.reviewed_by = current_user.username
    rec.reviewed_at = datetime.now(timezone.utc)
    log_audit(db, current_user, "reject", "quarantine_record", record_id, {})
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{record_id}", status_code=204)
def delete_quarantine_record(record_id: int, db: DbSession, current_user: AdminUser):
    rec = db.get(QuarantineRecord, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    log_audit(db, current_user, "delete", "quarantine_record", record_id, {})
    db.delete(rec)
    db.commit()
