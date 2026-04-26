from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create(client, name="Jan/2026", start="2026-01-01", end="2026-01-31"):
    r = client.post("/api/cycles", json={"name": name, "start_date": start, "end_date": end})
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# GET /api/cycles
# ---------------------------------------------------------------------------

class TestListCycles:
    def test_empty(self, client):
        assert client.get("/api/cycles").json() == []

    def test_lists_created_cycle(self, client):
        _create(client, name="Ciclo Visível")
        names = [c["name"] for c in client.get("/api/cycles").json()]
        assert "Ciclo Visível" in names

    def test_includes_record_count_zero(self, client):
        c = _create(client, name="SemRegistros")
        data = client.get("/api/cycles").json()
        found = next(x for x in data if x["id"] == c["id"])
        assert found["record_count"] == 0

    def test_includes_record_count_from_upload(self, client):
        c = _create(client, name="ComRegistros", start="2026-07-01", end="2026-07-31")
        csv = b"Colaborador,Data,Horas totais (decimal)\nAna,10/07/2026,8.0\n"
        client.post("/api/upload-timesheet", files={"file": ("t.csv", csv, "text/csv")})
        data = client.get("/api/cycles").json()
        found = next(x for x in data if x["id"] == c["id"])
        assert found["record_count"] == 1


# ---------------------------------------------------------------------------
# POST /api/cycles
# ---------------------------------------------------------------------------

class TestCreateCycle:
    def test_success(self, client):
        r = client.post("/api/cycles", json={
            "name": "Fev/2026", "start_date": "2026-02-01", "end_date": "2026-02-28"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Fev/2026"
        assert data["start_date"] == "2026-02-01"
        assert data["end_date"] == "2026-02-28"
        assert data["is_quarantine"] is False
        assert data["record_count"] == 0
        assert "id" in data

    def test_end_before_start_rejected(self, client):
        r = client.post("/api/cycles", json={
            "name": "Inv", "start_date": "2026-03-31", "end_date": "2026-03-01"
        })
        assert r.status_code == 422
        assert "end_date" in r.json()["detail"]

    def test_same_day_start_end_accepted(self, client):
        r = client.post("/api/cycles", json={
            "name": "Um dia", "start_date": "2026-04-15", "end_date": "2026-04-15"
        })
        assert r.status_code == 201

    def test_missing_name_rejected(self, client):
        r = client.post("/api/cycles", json={"start_date": "2026-01-01", "end_date": "2026-01-31"})
        assert r.status_code == 422

    def test_missing_dates_rejected(self, client):
        r = client.post("/api/cycles", json={"name": "Sem datas"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/cycles/{id}
# ---------------------------------------------------------------------------

class TestUpdateCycle:
    def test_success(self, client):
        c = _create(client, name="Original")
        r = client.put(f"/api/cycles/{c['id']}", json={
            "name": "Atualizado", "start_date": "2026-01-01", "end_date": "2026-01-31"
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Atualizado"

    def test_not_found(self, client):
        r = client.put("/api/cycles/99999", json={
            "name": "X", "start_date": "2026-01-01", "end_date": "2026-01-31"
        })
        assert r.status_code == 404

    def test_invalid_dates_rejected(self, client):
        c = _create(client, name="ParaAtualizar")
        r = client.put(f"/api/cycles/{c['id']}", json={
            "name": "ParaAtualizar", "start_date": "2026-01-31", "end_date": "2026-01-01"
        })
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/cycles/{id}
# ---------------------------------------------------------------------------

class TestDeleteCycle:
    def test_success(self, client):
        c = _create(client, name="ParaDeletar")
        assert client.delete(f"/api/cycles/{c['id']}").status_code == 204

    def test_not_found(self, client):
        assert client.delete("/api/cycles/99999").status_code == 404

    def test_deleted_absent_from_list(self, client):
        c = _create(client, name="SomeráDaLista")
        client.delete(f"/api/cycles/{c['id']}")
        ids = [x["id"] for x in client.get("/api/cycles").json()]
        assert c["id"] not in ids

    def test_blocked_when_has_records(self, client):
        _create(client, name="CicloComDados", start="2026-08-01", end="2026-08-31")
        csv = b"Colaborador,Data,Horas totais (decimal)\nBob,05/08/2026,8.0\n"
        client.post("/api/upload-timesheet", files={"file": ("t.csv", csv, "text/csv")})
        cycles = client.get("/api/cycles").json()
        target = next(x for x in cycles if x["name"] == "CicloComDados")
        r = client.delete(f"/api/cycles/{target['id']}")
        assert r.status_code == 409
        assert "registro" in r.json()["detail"]


# ---------------------------------------------------------------------------
# PATCH /api/cycles/{id}/toggle-status
# ---------------------------------------------------------------------------

class TestToggleStatus:
    def test_toggle_closes_open_cycle(self, client):
        c = _create(client, name="Fechável")
        assert c["is_closed"] is False
        r = client.patch(f"/api/cycles/{c['id']}/toggle-status")
        assert r.status_code == 200
        assert r.json()["is_closed"] is True

    def test_toggle_reopens_closed_cycle(self, client):
        c = _create(client, name="Reabrível")
        client.patch(f"/api/cycles/{c['id']}/toggle-status")
        r = client.patch(f"/api/cycles/{c['id']}/toggle-status")
        assert r.status_code == 200
        assert r.json()["is_closed"] is False

    def test_new_cycles_start_open(self, client):
        c = _create(client, name="Novo")
        assert c["is_closed"] is False

    def test_toggle_not_found(self, client):
        r = client.patch("/api/cycles/99999/toggle-status")
        assert r.status_code == 404
