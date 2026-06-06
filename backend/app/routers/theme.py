from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from backend.app.audit import log_audit
from backend.app.database import DbSession, _BUILTIN_PRESET_NAMES
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import GlobalConfig, ThemePreset
from backend.app.schemas import ThemePresetIn, ThemePresetOut, UIThemeIn, UIThemeOut
from backend.app.services.theme_svc import delete_logo, get_theme_out, save_logo

router = APIRouter(prefix="/api/theme", tags=["theme"])

MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB


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


@router.get("/presets", response_model=list[ThemePresetOut])
def list_presets(db: DbSession):
    """Public — no auth required. Built-ins first, then custom sorted by name."""
    rows = db.query(ThemePreset).order_by(
        ThemePreset.is_builtin.desc(), ThemePreset.name
    ).all()
    return rows


@router.post("/presets", response_model=ThemePresetOut, dependencies=[Depends(get_current_user)])
def upsert_preset(payload: ThemePresetIn, db: DbSession, current_user: AdminUser):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Nome do preset não pode ser vazio.")
    if name in _BUILTIN_PRESET_NAMES:
        raise HTTPException(status_code=400, detail="Não é possível sobrescrever um preset padrão.")
    existing = db.query(ThemePreset).filter_by(name=name).first()
    if existing:
        existing.config = payload.config
        db.commit()
        db.refresh(existing)
        log_audit(db, current_user, "update", "theme_preset", existing.id, {"name": name})
        db.commit()
        return existing
    preset = ThemePreset(name=name, is_builtin=False, config=payload.config)
    db.add(preset)
    db.flush()
    log_audit(db, current_user, "create", "theme_preset", preset.id, {"name": name})
    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/presets/{preset_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_preset(preset_id: int, db: DbSession, current_user: AdminUser):
    preset = db.get(ThemePreset, preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Preset não encontrado.")
    if preset.is_builtin:
        raise HTTPException(status_code=400, detail="Presets padrão não podem ser excluídos.")
    log_audit(db, current_user, "delete", "theme_preset", preset_id, {"name": preset.name})
    db.delete(preset)
    db.commit()


_PRESET_CSV_COLUMNS = [
    "name", "is_builtin",
    "color_primary", "color_background", "color_surface", "color_accent",
    "color_success", "color_warning", "color_danger", "color_text",
    "color_text_muted", "density",
    "pal_0", "pal_1", "pal_2", "pal_3", "pal_4", "pal_5", "pal_6", "pal_7",
    "color_card", "color_border", "color_text_hint", "color_violet", "border_radius",
]


@router.get("/presets/export", dependencies=[Depends(get_current_user)])
def export_presets(db: DbSession, _user: CurrentUser):
    presets = db.query(ThemePreset).order_by(
        ThemePreset.is_builtin.desc(), ThemePreset.name
    ).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_PRESET_CSV_COLUMNS)
    for p in presets:
        cfg = p.config or {}
        pal = cfg.get("chart_palette") or []
        writer.writerow([
            p.name,
            str(p.is_builtin).lower(),
            cfg.get("color_primary", ""),
            cfg.get("color_background", ""),
            cfg.get("color_surface", ""),
            cfg.get("color_accent", ""),
            cfg.get("color_success", ""),
            cfg.get("color_warning", ""),
            cfg.get("color_danger", ""),
            cfg.get("color_text", ""),
            cfg.get("color_text_muted", ""),
            cfg.get("density", "normal"),
            pal[0] if len(pal) > 0 else "",
            pal[1] if len(pal) > 1 else "",
            pal[2] if len(pal) > 2 else "",
            pal[3] if len(pal) > 3 else "",
            pal[4] if len(pal) > 4 else "",
            pal[5] if len(pal) > 5 else "",
            pal[6] if len(pal) > 6 else "",
            pal[7] if len(pal) > 7 else "",
            cfg.get("color_card", "") or "",
            cfg.get("color_border", "") or "",
            cfg.get("color_text_hint", "") or "",
            cfg.get("color_violet", "") or "",
            cfg.get("border_radius", "") or "",
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="theme_presets.csv"'},
    )


@router.post("/presets/import", dependencies=[Depends(get_current_user)])
def import_presets(file: UploadFile, db: DbSession, current_user: AdminUser):
    try:
        raw = file.file.read()
        if len(raw) > MAX_CSV_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo CSV excede o limite de 10 MB.")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Erro ao ler CSV: {exc}")

    created = updated = skipped = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            skipped += 1
            continue
        # Skip rows that are built-in or claim a built-in name
        is_builtin_flag = (row.get("is_builtin") or "").strip().lower()
        if is_builtin_flag == "true" or name in _BUILTIN_PRESET_NAMES:
            skipped += 1
            continue

        # Validate hex colors — require # prefix
        color_keys = [
            "color_primary", "color_background", "color_surface", "color_accent",
            "color_success", "color_warning", "color_danger", "color_text", "color_text_muted",
        ]
        cfg: dict = {}
        valid = True
        for key in color_keys:
            val = (row.get(key) or "").strip()
            if val and not val.startswith("#"):
                skipped += 1
                valid = False
                break
            cfg[key] = val
        if not valid:
            continue

        cfg["density"] = (row.get("density") or "normal").strip()
        palette = []
        for i in range(8):
            c = (row.get(f"pal_{i}") or "").strip()
            if c:
                palette.append(c)
        cfg["chart_palette"] = palette
        # Optional new fields
        for opt_key in ("color_card", "color_border", "color_text_hint", "color_violet"):
            val = (row.get(opt_key) or "").strip() or None
            cfg[opt_key] = val
        br = (row.get("border_radius") or "").strip() or None
        cfg["border_radius"] = br

        existing = db.query(ThemePreset).filter_by(name=name).first()
        if existing:
            existing.config = cfg
            updated += 1
        else:
            db.add(ThemePreset(name=name, is_builtin=False, config=cfg))
            created += 1

    if created or updated:
        log_audit(db, current_user, "import", "theme_preset", None,
                  {"created": created, "updated": updated, "skipped": skipped})
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped}
