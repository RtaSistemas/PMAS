from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models import AuditLog, User


def log_audit(
    db: Session,
    user: User,
    action: str,
    entity: str,
    entity_id: int | None = None,
    detail: dict | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
        timestamp=datetime.now(timezone.utc),
    ))
