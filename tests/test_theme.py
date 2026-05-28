from __future__ import annotations

import io

import pytest

from backend.app.database import _BUILTIN_PRESETS
from backend.app.models import ThemePreset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_CONFIG = {
    "color_primary": "#aabbcc", "color_background": "#000000",
    "color_surface": "#111111", "color_accent": "#ff00ff",
    "color_success": "#00ff00", "color_warning": "#ffff00",
    "color_danger": "#ff0000", "color_text": "#ffffff",
    "color_text_muted": "#888888", "density": "normal",
    "chart_palette": ["#aabbcc", "#112233"],
}


def _seed_builtins(db_session):
    """Insert the three built-in presets so tests that rely on them don't fail."""
    for p in _BUILTIN_PRESETS:
        if not db_session.query(ThemePreset).filter_by(name=p["name"]).first():
            db_session.add(ThemePreset(
                name=p["name"], is_builtin=p["is_builtin"], config=p["config"]
            ))
    db_session.commit()


class TestThemeGet:
    def test_get_theme_public(self, client):
        """GET /api/theme is public and returns default theme."""
        r = client.get("/api/theme")
        assert r.status_code == 200
        data = r.json()
        assert "color_primary" in data
        assert "app_name" in data
        assert "logo_url" in data

    def test_default_app_name(self, client):
        data = client.get("/api/theme").json()
        assert data["app_name"] == "PMAS"

    def test_default_logo_url_is_none(self, client):
        data = client.get("/api/theme").json()
        assert data["logo_url"] is None


class TestThemePut:
    def test_update_theme(self, client):
        payload = {
            "app_name": "MyApp",
            "color_primary": "#ff0000",
            "color_background": "#000000",
            "color_surface": "#111111",
            "color_accent": "#ff00ff",
            "color_success": "#00ff00",
            "color_warning": "#ffff00",
            "color_danger": "#ff0000",
            "color_text": "#ffffff",
            "color_text_muted": "#888888",
            "density": "compact",
            "chart_palette": ["#ff0000", "#00ff00"],
        }
        r = client.put("/api/theme", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["app_name"] == "MyApp"
        assert data["color_primary"] == "#ff0000"
        assert data["density"] == "compact"

    def test_updated_theme_persists(self, client):
        client.put("/api/theme", json={
            "app_name": "Branded", "color_primary": "#123456",
            "color_background": "#000000", "color_surface": "#111111",
            "color_accent": "#ff00ff", "color_success": "#00ff00",
            "color_warning": "#ffff00", "color_danger": "#ff0000",
            "color_text": "#ffffff", "color_text_muted": "#888888",
            "density": "normal", "chart_palette": [],
        })
        data = client.get("/api/theme").json()
        assert data["app_name"] == "Branded"
        assert data["color_primary"] == "#123456"


class TestThemePresets:
    def test_list_presets_returns_builtins(self, client, db_session):
        _seed_builtins(db_session)
        r = client.get("/api/theme/presets")
        assert r.status_code == 200
        data = r.json()
        names = [p["name"] for p in data]
        assert "Padrão PMAS" in names
        assert "Azul Corporativo" in names
        assert "Alto Contraste" in names
        assert len(data) >= 3

    def test_list_presets_builtins_first(self, client, db_session):
        _seed_builtins(db_session)
        # Add a custom preset that would sort before built-ins alphabetically
        client.post("/api/theme/presets", json={"name": "AAAA Custom", "config": _SAMPLE_CONFIG})
        r = client.get("/api/theme/presets")
        data = r.json()
        builtin_indices = [i for i, p in enumerate(data) if p["is_builtin"]]
        custom_indices  = [i for i, p in enumerate(data) if not p["is_builtin"]]
        assert max(builtin_indices) < min(custom_indices)

    def test_create_custom_preset(self, client):
        r = client.post("/api/theme/presets", json={"name": "Meu Preset", "config": _SAMPLE_CONFIG})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Meu Preset"
        assert data["is_builtin"] is False
        assert data["id"] > 0

    def test_create_custom_preset_upsert(self, client):
        """POST with an existing custom name updates it instead of creating a duplicate."""
        client.post("/api/theme/presets", json={"name": "Upsert Test", "config": _SAMPLE_CONFIG})
        updated_config = {**_SAMPLE_CONFIG, "color_primary": "#123456"}
        r2 = client.post("/api/theme/presets", json={"name": "Upsert Test", "config": updated_config})
        assert r2.status_code == 200
        assert r2.json()["config"]["color_primary"] == "#123456"
        # Only one row in the list
        listed = [p for p in client.get("/api/theme/presets").json() if p["name"] == "Upsert Test"]
        assert len(listed) == 1

    def test_create_preset_with_builtin_name_returns_400(self, client, db_session):
        _seed_builtins(db_session)
        r = client.post("/api/theme/presets", json={"name": "Padrão PMAS", "config": _SAMPLE_CONFIG})
        assert r.status_code == 400

    def test_create_preset_empty_name_returns_422(self, client):
        r = client.post("/api/theme/presets", json={"name": "  ", "config": _SAMPLE_CONFIG})
        assert r.status_code == 422

    def test_delete_custom_preset(self, client):
        r = client.post("/api/theme/presets", json={"name": "Del Me", "config": _SAMPLE_CONFIG})
        preset_id = r.json()["id"]
        r2 = client.delete(f"/api/theme/presets/{preset_id}")
        assert r2.status_code == 204
        listed = [p for p in client.get("/api/theme/presets").json() if p["name"] == "Del Me"]
        assert len(listed) == 0

    def test_delete_custom_preset_not_found(self, client):
        r = client.delete("/api/theme/presets/99999")
        assert r.status_code == 404

    def test_delete_builtin_returns_400(self, client, db_session):
        _seed_builtins(db_session)
        presets = client.get("/api/theme/presets").json()
        builtin = next(p for p in presets if p["is_builtin"])
        r = client.delete(f"/api/theme/presets/{builtin['id']}")
        assert r.status_code == 400

    def test_export_presets_csv(self, client, db_session):
        _seed_builtins(db_session)
        r = client.get("/api/theme/presets/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]
        lines = r.text.strip().split("\n")
        header = lines[0].strip()
        expected_cols = [
            "name", "is_builtin", "color_primary", "color_background",
            "color_surface", "color_accent", "color_success", "color_warning",
            "color_danger", "color_text", "color_text_muted", "density",
            "pal_0", "pal_1", "pal_2", "pal_3", "pal_4", "pal_5",
        ]
        for col in expected_cols:
            assert col in header
        # At least 3 data rows (the built-ins)
        assert len(lines) >= 4

    def test_import_presets_csv_creates(self, client):
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            "Imported Preset,false,#001122,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,#001122,#334455,#667788,#99aabb,#ccddef,#001234\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == 1
        assert data["updated"] == 0
        assert data["skipped"] == 0

    def test_import_presets_csv_skips_builtins(self, client):
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            "Padrão PMAS,false,#001122,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,#001122,#334455,#667788,#99aabb,#ccddef,#001234\r\n"
            "Skip Me,true,#001122,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,#001122,#334455,#667788,#99aabb,#ccddef,#001234\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        # Both rows skipped: first has builtin name, second has is_builtin=true
        assert data["skipped"] == 2
        assert data["created"] == 0

    def test_import_presets_csv_updates_existing(self, client):
        client.post("/api/theme/presets", json={"name": "Update Me", "config": _SAMPLE_CONFIG})
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            "Update Me,false,#aabbcc,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,relaxed,#001122,#334455,#667788,#99aabb,#ccddef,#001234\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["updated"] == 1
        assert data["created"] == 0

    def test_import_presets_invalid_hex_skipped(self, client):
        """Row with a color value missing the # prefix is skipped."""
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            # color_primary is missing the leading #
            "Bad Hex,false,aabbcc,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,,,,,,"
            "\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["skipped"] == 1
        assert data["created"] == 0

    def test_import_presets_empty_name_skipped(self, client):
        """Row with an empty name is skipped."""
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            ",false,#001122,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,,,,,,"
            "\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["skipped"] == 1
        assert data["created"] == 0

    def test_import_presets_mixed_valid_invalid(self, client):
        """Valid rows are still created even when mixed with invalid rows."""
        csv_content = (
            "name,is_builtin,color_primary,color_background,color_surface,"
            "color_accent,color_success,color_warning,color_danger,color_text,"
            "color_text_muted,density,pal_0,pal_1,pal_2,pal_3,pal_4,pal_5\r\n"
            # Valid row
            "Good Preset,false,#001122,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,#001122,#334455,#667788,#99aabb,#ccddef,#001234\r\n"
            # Invalid: missing # on color_primary
            "Bad Preset,false,aabbcc,#000000,#111111,"
            "#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,"
            "#888888,normal,,,,,,"
            "\r\n"
        )
        r = client.post(
            "/api/theme/presets/import",
            files={"file": ("presets.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["created"] == 1
        assert data["skipped"] == 1


class TestThemeLogo:
    def test_upload_logo_sets_logo_url(self, client):
        """POST /api/theme/logo with a valid PNG sets logo_url in GET /api/theme."""
        client.get("/api/theme")  # ensure GlobalConfig id=1 exists

        r = client.post(
            "/api/theme/logo",
            files={"file": ("logo.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        )
        assert r.status_code == 200
        assert r.json()["logo_url"] is not None

        # Subsequent GET also reflects the change
        r2 = client.get("/api/theme")
        assert r2.json()["logo_url"] is not None

    def test_delete_logo_clears_logo_url(self, client):
        """DELETE /api/theme/logo resets logo_url to None."""
        client.get("/api/theme")  # ensure GlobalConfig exists
        client.post(
            "/api/theme/logo",
            files={"file": ("logo.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        )

        r = client.delete("/api/theme/logo")
        assert r.status_code == 200
        assert r.json()["logo_url"] is None

        r2 = client.get("/api/theme")
        assert r2.json()["logo_url"] is None

    def test_upload_logo_invalid_extension_returns_400(self, client):
        """POST /api/theme/logo with a disallowed extension returns 400."""
        client.get("/api/theme")

        r = client.post(
            "/api/theme/logo",
            files={"file": ("document.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert r.status_code == 400
