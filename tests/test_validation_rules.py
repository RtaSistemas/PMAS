from __future__ import annotations

import pytest


class TestValidationRules:
    def test_list_includes_system_rules(self, client):
        r = client.get("/api/validation-rules")
        assert r.status_code == 200
        rules = r.json()
        assert len(rules) >= 6
        system_rules = [x for x in rules if x["is_system"]]
        assert len(system_rules) == 6

    def test_create_custom_rule(self, client):
        payload = {
            "field": "horas_individuais",
            "operator": "gt",
            "value": "12",
            "action": "warning",
            "order": 20,
            "is_active": True,
            "description": "Test rule",
        }
        r = client.post("/api/validation-rules", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["field"] == "horas_individuais"
        assert data["is_system"] is False
        assert data["id"] is not None

    def test_create_aggregate_rule_quarentena_rejected(self, client):
        payload = {
            "field": "soma_diaria",
            "operator": "gt",
            "value": "30",
            "action": "quarentena",
            "order": 20,
            "is_active": True,
        }
        r = client.post("/api/validation-rules", json=payload)
        assert r.status_code == 422  # validator rejects quarentena for aggregate

    def test_update_custom_rule(self, client):
        # Create first
        created = client.post("/api/validation-rules", json={
            "field": "horas_individuais", "operator": "gt", "value": "10",
            "action": "warning", "order": 20, "is_active": True,
        }).json()
        rule_id = created["id"]

        # Update
        r = client.put(f"/api/validation-rules/{rule_id}", json={
            "field": "horas_individuais", "operator": "gt", "value": "15",
            "action": "warning", "order": 20, "is_active": True,
        })
        assert r.status_code == 200
        assert r.json()["value"] == "15"

    def test_system_rule_immutable_fields_rejected(self, client):
        rules = client.get("/api/validation-rules").json()
        # Pick a system rule whose action is not already "info"
        sys_rule = next(x for x in rules if x["is_system"] and x["action"] != "info")
        r = client.put(f"/api/validation-rules/{sys_rule['id']}", json={
            "field": sys_rule["field"], "operator": sys_rule["operator"],
            "value": sys_rule["value"], "action": "info",  # changed → 422
            "order": sys_rule["order"], "is_active": sys_rule["is_active"],
        })
        assert r.status_code == 422

    def test_system_rule_value_editable(self, client):
        rules = client.get("/api/validation-rules").json()
        sys_rule = next(x for x in rules if x["is_system"])
        r = client.put(f"/api/validation-rules/{sys_rule['id']}", json={
            "field": sys_rule["field"], "operator": sys_rule["operator"],
            "value": "30", "action": sys_rule["action"],
            "order": sys_rule["order"], "is_active": sys_rule["is_active"],
        })
        assert r.status_code == 200
        assert r.json()["value"] == "30"

    def test_delete_custom_rule(self, client):
        created = client.post("/api/validation-rules", json={
            "field": "horas_individuais", "operator": "gt", "value": "10",
            "action": "warning", "order": 20, "is_active": True,
        }).json()
        rule_id = created["id"]
        r = client.delete(f"/api/validation-rules/{rule_id}")
        assert r.status_code == 204

        # Verify gone
        rules = client.get("/api/validation-rules").json()
        assert not any(x["id"] == rule_id for x in rules)

    def test_cannot_delete_system_rule(self, client):
        rules = client.get("/api/validation-rules").json()
        sys_rule = next(x for x in rules if x["is_system"])
        r = client.delete(f"/api/validation-rules/{sys_rule['id']}")
        assert r.status_code == 403

    def test_toggle_system_rule(self, client):
        rules = client.get("/api/validation-rules").json()
        sys_rule = next(x for x in rules if x["is_system"])
        original = sys_rule["is_active"]
        r = client.patch(f"/api/validation-rules/{sys_rule['id']}/toggle")
        assert r.status_code == 200
        assert r.json()["is_active"] is not original
        # Restore
        client.patch(f"/api/validation-rules/{sys_rule['id']}/toggle")

    def test_reorder_rules(self, client):
        r1 = client.post("/api/validation-rules", json={
            "field": "horas_individuais", "operator": "gt", "value": "10",
            "action": "warning", "order": 10, "is_active": True,
        }).json()
        r2 = client.post("/api/validation-rules", json={
            "field": "horas_individuais", "operator": "lt", "value": "0",
            "action": "warning", "order": 20, "is_active": True,
        }).json()

        r = client.post("/api/validation-rules/reorder", json={r1["id"]: 50, r2["id"]: 5})
        assert r.status_code == 200

        # r2 should now come first (order=5)
        rules = client.get("/api/validation-rules").json()
        custom = [x for x in rules if not x["is_system"]]
        orders = {x["id"]: x["order"] for x in custom}
        assert orders[r2["id"]] < orders[r1["id"]]
