from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

from backend.app.audit import log_audit
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
def update_theme(payload: UIThemeIn, db: DbSession, current_user: AdminUser):
    cfg = db.get(GlobalConfig, 1)
    if cfg is None:
        cfg = GlobalConfig(id=1)
        db.add(cfg)
    cfg.ui_theme = payload.model_dump(exclude={"chart_palette"}) | {
        "chart_palette": payload.chart_palette
    }
    db.commit()
    log_audit(db, current_user, "update", "ui_theme", 1, payload.model_dump())
    db.commit()
    return get_theme_out(db)


@router.post("/logo", response_model=UIThemeOut, dependencies=[Depends(get_current_user)])
async def upload_logo(file: UploadFile, db: DbSession, current_user: AdminUser):
    await save_logo(file, db)
    log_audit(db, current_user, "import", "ui_theme_logo", 1, {"filename": file.filename})
    db.commit()
    return get_theme_out(db)


@router.delete("/logo", response_model=UIThemeOut, dependencies=[Depends(get_current_user)])
def remove_logo(db: DbSession, current_user: AdminUser):
    delete_logo(db)
    log_audit(db, current_user, "delete", "ui_theme_logo", 1, {})
    db.commit()
    return get_theme_out(db)
