from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import AuditLog
from backend.app.schemas import AuditLogItem

router = APIRouter(prefix="/api", tags=["auditlog"], dependencies=[Depends(get_current_user)])


@router.get("/audit-log", summary="Log de auditoria (admin)", response_model=list[AuditLogItem])
def get_audit_log(
    db: DbSession,
    _admin: AdminUser,
    entity: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    q = db.query(AuditLog)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if action:
        q = q.filter(AuditLog.action == action)
    return (
        q.order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
