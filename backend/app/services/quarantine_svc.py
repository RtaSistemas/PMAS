from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import QuarantineRecord


def create_quarantine_record(
    db: Session,
    upload_session_id: int | None,
    user_id: int | None,
    username: str | None,
    raw_data: dict,
    reason: str,
    rule_id: int | None = None,
) -> QuarantineRecord:
    """Stage a QuarantineRecord in the session — caller owns the transaction."""
    qr = QuarantineRecord(
        upload_session_id=upload_session_id,
        uploaded_by_user_id=user_id,
        uploaded_by_username=username,
        raw_data=raw_data,
        quarantine_reason=reason,
        rule_id=rule_id,
    )
    db.add(qr)
    return qr
