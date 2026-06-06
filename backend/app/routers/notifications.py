from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import Notification

router = APIRouter(
    prefix="/api/my/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_user)],
)


class NotificationOut(BaseModel):
    id: int
    message: str
    level: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[NotificationOut])
def list_notifications(db: DbSession, current_user: CurrentUser):
    """Return up to 50 notifications for the authenticated user, newest first."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, db: DbSession, current_user: CurrentUser):
    """Mark a single notification as read."""
    notif = db.get(Notification, notification_id)
    if notif is None or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificação não encontrada.")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/read-all")
def mark_all_read(db: DbSession, current_user: CurrentUser):
    """Mark all notifications as read for the current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.delete("/{notification_id}", status_code=204)
def delete_notification(notification_id: int, db: DbSession, current_user: CurrentUser):
    """Delete a single notification belonging to the current user."""
    notif = db.get(Notification, notification_id)
    if notif is None or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificação não encontrada.")
    db.delete(notif)
    db.commit()
