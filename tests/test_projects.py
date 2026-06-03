from __future__ import annotations


def _create(client, pep="TST-001", **kwargs):
    r = client.post("/api/projects", json={"pep_wbs": pep, **kwargs})
    assert r.status_code == 201
    return r.json()


class TestListProjects:
    def test_empty(self, client):
        assert client.get("/api/projects").json() == []

    def test_returns_created(self, client):
        _create(client, pep="LST-001", name="Projeto Lista")
        peps = [p["pep_wbs"] for p in client.get("/api/projects").json()]
        assert "LST-001" in peps

    def test_sorted_by_pep(self, client):
        _create(client, pep="ZZZ-999")
        _create(client, pep="AAA-001")
        peps = [p["pep_wbs"] for p in client.get("/api/projects").json()]
        assert peps.index("AAA-001") < peps.index("ZZZ-999")


class TestCreateProject:
    def test_minimal(self, client):
        r = client.post("/api/projects", json={"pep_wbs": "MIN-001"})
        assert r.status_code == 201
        d = r.json()
        assert d["pep_wbs"] == "MIN-001"
        assert d["status"] == "ativo"
        assert d["budget_hours"] is None
        assert d["name"] is None

    def test_full(self, client):
        r = client.post("/api/projects", json={
            "pep_wbs": "FUL-001",
            "name": "Completo",
            "client": "Cliente X",
            "manager": "Gerente Y",
            "budget_hours": 320.0,
            "status": "ativo",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["budget_hours"] == 320.0
        assert d["client"] == "Cliente X"

    def test_duplicate_pep_rejected(self, client):
        _create(client, pep="DUP-001")
        r = client.post("/api/projects", json={"pep_wbs": "DUP-001"})
        assert r.status_code == 409

    def test_missing_pep_rejected(self, client):
        r = client.post("/api/projects", json={"name": "Sem PEP"})
        assert r.status_code == 422

    def test_status_values(self, client):
        for status in ("ativo", "suspenso", "encerrado"):
            r = client.post("/api/projects", json={"pep_wbs": f"STS-{status}", "status": status})
            assert r.status_code == 201
            assert r.json()["status"] == status


class TestUpdateProject:
    def test_success(self, client):
        p = _create(client, pep="UPD-001", name="Original")
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "UPD-001", "name": "Atualizado", "status": "encerrado"
        })
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "Atualizado"
        assert d["status"] == "encerrado"

    def test_update_budget(self, client):
        p = _create(client, pep="BUD-001")
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BUD-001", "status": "ativo", "budget_hours": 500.0
        })
        assert r.status_code == 200
        assert r.json()["budget_hours"] == 500.0

    def test_not_found(self, client):
        r = client.put("/api/projects/99999", json={"pep_wbs": "X", "status": "ativo"})
        assert r.status_code == 404

    def test_pep_conflict_with_other(self, client):
        p1 = _create(client, pep="CONF-001")
        p2 = _create(client, pep="CONF-002")
        r = client.put(f"/api/projects/{p2['id']}", json={"pep_wbs": "CONF-001", "status": "ativo"})
        assert r.status_code == 409

    def test_same_pep_on_self_allowed(self, client):
        p = _create(client, pep="SELF-001", name="Original")
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "SELF-001", "name": "Atualizado", "status": "ativo"
        })
        assert r.status_code == 200


class TestProjectDates:
    def test_create_with_dates(self, client):
        r = client.post("/api/projects", json={
            "pep_wbs": "DT-001",
            "start_date": "2025-01-01",
            "planned_end_date": "2025-12-31",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["start_date"] == "2025-01-01"
        assert d["planned_end_date"] == "2025-12-31"
        assert d["completion_date"] is None

    def test_completion_date_forces_encerrado(self, client):
        r = client.post("/api/projects", json={
            "pep_wbs": "DT-002",
            "status": "ativo",
            "completion_date": "2025-06-30",
        })
        assert r.status_code == 201
        assert r.json()["status"] == "encerrado"
        assert r.json()["completion_date"] == "2025-06-30"

    def test_update_sets_completion_date(self, client):
        p = _create(client, pep="DT-003", status="ativo")
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "DT-003",
            "status": "ativo",
            "completion_date": "2025-09-15",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "encerrado"
        assert d["completion_date"] == "2025-09-15"

    def test_dates_null_by_default(self, client):
        r = client.post("/api/projects", json={"pep_wbs": "DT-004"})
        assert r.status_code == 201
        d = r.json()
        assert d["start_date"] is None
        assert d["planned_end_date"] is None
        assert d["completion_date"] is None


class TestDeleteProject:
    def test_success(self, client):
        p = _create(client, pep="DEL-001")
        assert client.delete(f"/api/projects/{p['id']}").status_code == 204

    def test_not_found(self, client):
        assert client.delete("/api/projects/99999").status_code == 404

    def test_deleted_not_in_list(self, client):
        p = _create(client, pep="DEL-002")
        client.delete(f"/api/projects/{p['id']}")
        peps = [x["pep_wbs"] for x in client.get("/api/projects").json()]
        assert "DEL-002" not in peps


class TestBudgetRevisionHistory:
    def test_no_history_returns_empty(self, client):
        p = _create(client, pep="BRH-001")
        r = client.get(f"/api/projects/{p['id']}/budget-history")
        assert r.status_code == 200
        assert r.json() == []

    def test_revision_created_on_budget_hours_change(self, client):
        p = _create(client, pep="BRH-002", budget_hours=100.0)
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-002", "status": "ativo", "budget_hours": 200.0,
        })
        assert r.status_code == 200
        history = client.get(f"/api/projects/{p['id']}/budget-history").json()
        assert len(history) == 1
        rev = history[0]
        assert rev["old_budget_hours"] == 100.0
        assert rev["new_budget_hours"] == 200.0
        assert rev["changed_by"] == "test_admin"

    def test_revision_created_on_budget_cost_change(self, client):
        p = _create(client, pep="BRH-003", budget_cost=5000.0)
        r = client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-003", "status": "ativo", "budget_cost": 9000.0,
        })
        assert r.status_code == 200
        history = client.get(f"/api/projects/{p['id']}/budget-history").json()
        assert len(history) == 1
        rev = history[0]
        assert rev["old_budget_cost"] == 5000.0
        assert rev["new_budget_cost"] == 9000.0
        assert rev["changed_by"] == "test_admin"

    def test_no_revision_when_budget_unchanged(self, client):
        p = _create(client, pep="BRH-004", budget_hours=100.0, budget_cost=5000.0)
        # Update only the name — budget unchanged
        client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-004", "status": "ativo",
            "budget_hours": 100.0, "budget_cost": 5000.0, "name": "Novo Nome",
        })
        history = client.get(f"/api/projects/{p['id']}/budget-history").json()
        assert len(history) == 0

    def test_reason_stored(self, client):
        p = _create(client, pep="BRH-005", budget_hours=100.0)
        client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-005", "status": "ativo", "budget_hours": 150.0,
            "budget_change_reason": "Replanejamento Q2",
        })
        history = client.get(f"/api/projects/{p['id']}/budget-history").json()
        assert len(history) == 1
        assert history[0]["reason"] == "Replanejamento Q2"

    def test_multiple_revisions_ordered_desc(self, client):
        p = _create(client, pep="BRH-006", budget_hours=100.0)
        client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-006", "status": "ativo", "budget_hours": 200.0,
        })
        client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-006", "status": "ativo", "budget_hours": 300.0,
        })
        client.put(f"/api/projects/{p['id']}", json={
            "pep_wbs": "BRH-006", "status": "ativo", "budget_hours": 400.0,
        })
        history = client.get(f"/api/projects/{p['id']}/budget-history").json()
        assert len(history) == 3
        # Most recent first: 300→400, 200→300, 100→200
        assert history[0]["new_budget_hours"] == 400.0
        assert history[1]["new_budget_hours"] == 300.0
        assert history[2]["new_budget_hours"] == 200.0

    def test_404_on_unknown_project(self, client):
        r = client.get("/api/projects/99999/budget-history")
        assert r.status_code == 404
