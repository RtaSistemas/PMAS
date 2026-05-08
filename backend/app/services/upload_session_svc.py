from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import UploadSession


def create_upload_session(
    db: Session,
    user_id: int | None,
    username: str,
    source_file: str,
    status: str,
    inserted: int,
    skipped: int,
    quarantine: int,
    warning_count: int,
    info_count: int,
    warnings: list[str],
    infos: list[str],
) -> UploadSession:
    """Add UploadSession to session and flush to get id — caller owns commit."""
    session = UploadSession(
        uploaded_by_user_id=user_id,
        uploaded_by_username=username,
        source_file=source_file,
        status=status,
        records_inserted=inserted,
        records_skipped=skipped,
        quarantine_added=quarantine,
        warning_count=warning_count,
        info_count=info_count,
        warnings_detail=warnings or None,
        infos_detail=infos or None,
    )
    db.add(session)
    db.flush()
    return session
