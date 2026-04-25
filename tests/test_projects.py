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
