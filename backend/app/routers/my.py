from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from backend.app.database import DbSession
from backend.app.deps import CurrentUser, get_current_user
from backend.app.models import UserPreference
from backend.app.schemas import UserPreferenceIn, UserPreferenceOut

router = APIRouter(
    prefix="/api/my",
    tags=["my"],
    dependencies=[Depends(get_current_user)],
)


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
