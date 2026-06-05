from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models import Notification


def create_notification(
    db: Session,
    user_id: int,
    message: str,
    level: str = "info",
) -> Notification:
    """Create a Notification and add it to the session. Caller must commit."""
    notif = Notification(user_id=user_id, message=message, level=level)
    db.add(notif)
    return notif
