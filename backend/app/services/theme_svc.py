from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.models import GlobalConfig
from backend.app.schemas import UIThemeOut

LOGO_DIR = Path(__file__).resolve().parents[3] / "static" / "assets" / "logos"
ALLOWED_EXT: frozenset[str] = frozenset({".png", ".jpg", ".jpeg", ".svg", ".webp"})
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({
    "image/png", "image/jpeg", "image/svg+xml", "image/webp",
})
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
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    if ctype and ctype not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não permitido: {ctype}")
    data = await file.read(MAX_LOGO_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="O arquivo de logo está vazio.")
    if len(data) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="Logo excede o limite de 2 MB.")
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    from uuid import uuid4
    filename = f"logo_{uuid4().hex}{ext}"
    dest = LOGO_DIR / filename
    dest.write_bytes(data)
    cfg = db.get(GlobalConfig, 1)
    if cfg is None:
        cfg = GlobalConfig(id=1)
        db.add(cfg)
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
    # The endpoint is public: stored values that no longer validate (older
    # data) must fall back to defaults instead of breaking every page load.
    for _ in range(len(merged) + 1):
        try:
            return UIThemeOut(**merged)
        except ValidationError as exc:
            bad = {e["loc"][0] for e in exc.errors() if e.get("loc")}
            if not bad:
                break
            for key in bad:
                if key in DEFAULT_THEME:
                    merged[key] = DEFAULT_THEME[key]
                else:
                    merged.pop(key, None)
    return UIThemeOut(**DEFAULT_THEME, logo_url=logo_url)


def delete_logo(db: Session) -> None:
    cfg = db.get(GlobalConfig, 1)
    if cfg and cfg.logo_path:
        p = Path(cfg.logo_path)
        if p.exists():
            p.unlink(missing_ok=True)
        cfg.logo_path = None
        db.commit()
