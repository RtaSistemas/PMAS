from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import ProjectAlert
from backend.app.schemas import ProjectAlertOut
from backend.app.utils import now_br

router = APIRouter(
    prefix="/api/project-alerts",
    tags=["project-alerts"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[ProjectAlertOut])
def list_project_alerts(
    db: DbSession,
    _current_user: AdminUser,
    pep_wbs: str | None = None,
    alert_type: str | None = None,
    is_resolved: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=200, le=1000),
    offset: int = 0,
):
    """List all ProjectAlerts (admin only). Supports filtering by PEP, type, resolved status, and date range."""
    q = db.query(ProjectAlert).order_by(ProjectAlert.created_at.desc())
    if pep_wbs is not None:
        q = q.filter(ProjectAlert.pep_wbs == pep_wbs)
    if alert_type is not None:
        q = q.filter(ProjectAlert.alert_type == alert_type)
    if is_resolved is not None:
        q = q.filter(ProjectAlert.is_resolved == is_resolved)
    if date_from is not None:
        q = q.filter(ProjectAlert.created_at >= date_from)
    if date_to is not None:
        q = q.filter(ProjectAlert.created_at <= date_to + " 23:59:59")
    return q.offset(offset).limit(limit).all()
