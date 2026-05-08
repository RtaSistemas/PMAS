from __future__ import annotations

import pytest


class TestMyPreferences:
    def test_get_empty_preferences(self, client):
        r = client.get("/api/my/preferences")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == 9999  # mock admin id
        assert data["dashboard"] is None

    def test_save_preferences(self, client):
        payload = {"dashboard": {"chart_order": ["effort", "portfolio", "forecast"]}}
        r = client.put("/api/my/preferences", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["dashboard"]["chart_order"] == ["effort", "portfolio", "forecast"]
        assert data["updated_at"] is not None

    def test_overwrite_preferences(self, client):
        client.put("/api/my/preferences", json={"dashboard": {"chart_order": ["a", "b"]}})
        r = client.put("/api/my/preferences", json={"dashboard": {"chart_order": ["b", "a"]}})
        assert r.status_code == 200
        assert r.json()["dashboard"]["chart_order"] == ["b", "a"]

    def test_get_returns_saved_preferences(self, client):
        client.put("/api/my/preferences", json={"dashboard": {"layout": "compact"}})
        r = client.get("/api/my/preferences")
        assert r.status_code == 200
        assert r.json()["dashboard"]["layout"] == "compact"

    def test_null_dashboard_accepted(self, client):
        r = client.put("/api/my/preferences", json={"dashboard": None})
        assert r.status_code == 200
        assert r.json()["dashboard"] is None
