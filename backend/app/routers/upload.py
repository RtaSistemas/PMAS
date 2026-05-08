from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import UploadSession
from backend.app.schemas import UploadSessionOut

router = APIRouter(
    prefix="/api/upload-history",
    tags=["upload-history"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[UploadSessionOut])
def list_upload_sessions(db: DbSession, _: AdminUser, limit: int = 200, offset: int = 0):
    return (
        db.query(UploadSession)
        .order_by(UploadSession.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{session_id}", response_model=UploadSessionOut)
def get_upload_session(session_id: int, db: DbSession, _: AdminUser):
    from fastapi import HTTPException
    session = db.get(UploadSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return session
