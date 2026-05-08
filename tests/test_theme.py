from __future__ import annotations

import pytest


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
