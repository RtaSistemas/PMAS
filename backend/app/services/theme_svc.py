from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.models import GlobalConfig
from backend.app.schemas import UIThemeOut

LOGO_DIR = Path(__file__).resolve().parents[3] / "static" / "assets" / "logos"
ALLOWED_EXT: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"})
MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB

DEFAULT_THEME: dict = {
    "app_name": "PMAS",
    "color_primary": "#4f8ef7",
    "color_background": "#081122",
    "color_surface": "#0e2038",
    "color_accent": "#07b3d7",
    "color_success": "#5ad388",
    "color_warning": "#d9b273",
    "color_danger": "#c56d76",
    "color_text": "#e0e0e0",
    "color_text_muted": "#818998",
    "density": "normal",
    "chart_palette": ["#4f8ef7", "#d9b273", "#a78bfa", "#35a1f3", "#5ad388", "#01c1b9"],
}


async def save_logo(file: UploadFile, db: Session) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Extensão não permitida: {ext}")
    data = await file.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="Logo excede o limite de 2 MB.")
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    from uuid import uuid4
    filename = f"logo_{uuid4().hex}{ext}"
    dest = LOGO_DIR / filename
    dest.write_bytes(data)
    cfg = db.get(GlobalConfig, 1)
    if cfg.logo_path:
        old = Path(cfg.logo_path)
        if old.exists():
            old.unlink(missing_ok=True)
    cfg.logo_path = str(dest)
    db.commit()
    return f"/static/assets/logos/{filename}"


def get_theme_out(db: Session) -> UIThemeOut:
    cfg = db.get(GlobalConfig, 1)
    theme = cfg.ui_theme or {} if cfg else {}
    logo_url: str | None = None
    if cfg and cfg.logo_path:
        logo_url = f"/static/assets/logos/{Path(cfg.logo_path).name}"
    merged = {**DEFAULT_THEME, **theme, "logo_url": logo_url}
    return UIThemeOut(**merged)


def delete_logo(db: Session) -> None:
    cfg = db.get(GlobalConfig, 1)
    if cfg and cfg.logo_path:
        p = Path(cfg.logo_path)
        if p.exists():
            p.unlink(missing_ok=True)
        cfg.logo_path = None
        db.commit()
