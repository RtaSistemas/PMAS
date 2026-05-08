from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import GlobalConfig
from backend.app.schemas import UIThemeIn, UIThemeOut
from backend.app.services.theme_svc import delete_logo, get_theme_out, save_logo

router = APIRouter(prefix="/api/theme", tags=["theme"])


@router.get("", response_model=UIThemeOut)
def get_theme(db: DbSession):
    """Public endpoint — no authentication required."""
    cfg = db.get(GlobalConfig, 1)
    if cfg is None:
        cfg = GlobalConfig(id=1)
        db.add(cfg)
        db.commit()
    return get_theme_out(db)


@router.put("", response_model=UIThemeOut, dependencies=[Depends(get_current_user)])
def update_theme(payload: UIThemeIn, db: DbSession, _: AdminUser):
    cfg = db.get(GlobalConfig, 1)
    if cfg is None:
        cfg = GlobalConfig(id=1)
        db.add(cfg)
    cfg.ui_theme = payload.model_dump(exclude={"chart_palette"}) | {
        "chart_palette": payload.chart_palette
    }
    db.commit()
    return get_theme_out(db)


@router.post("/logo", response_model=UIThemeOut, dependencies=[Depends(get_current_user)])
async def upload_logo(file: UploadFile, db: DbSession, _: AdminUser):
    await save_logo(file, db)
    return get_theme_out(db)


@router.delete("/logo", response_model=UIThemeOut, dependencies=[Depends(get_current_user)])
def remove_logo(db: DbSession, _: AdminUser):
    delete_logo(db)
    return get_theme_out(db)
