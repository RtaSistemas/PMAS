"""Regression tests for the CRUD audit findings (C1..C19)."""
from __future__ import annotations

import asyncio
import io
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app.models import (
    Collaborator, Cycle, Project, ProjectCyclePlan, RateCard, SeniorityLevel,
    TimesheetRecord, User, ValidationRule,
)
from backend.app.routers.auth import hash_password, verify_password


def _csv(client, url, text, name="f.csv"):
    return client.post(url, files={"file": (name, io.BytesIO(text.encode()), "text/csv")})


def _cycle(client, name="Jan/2026", start="2026-01-01", end="2026-01-31"):
    r = client.post("/api/cycles", json={"name": name, "start_date": start, "end_date": end})
    assert r.status_code == 201, r.text
    return r.json()


def _project(client, pep="P-1", **kw):
    r = client.post("/api/projects", json={"pep_wbs": pep, **kw})
    assert r.status_code == 201, r.text
    return r.json()


def _level(db, name="Pleno"):
    sl = SeniorityLevel(name=name)
    db.add(sl)
    db.commit()
    db.refresh(sl)
    return sl


# ---------------------------------------------------------------------------
# C1 — delete cycle with plans / other parents
# ---------------------------------------------------------------------------

class TestC1DeleteParents:
    def test_delete_cycle_with_plans_is_409(self, client):
        c = _cycle(client)
        p = _project(client)
        assert client.put(f"/api/projects/{p['id']}/plans/{c['id']}",
                          json={"cycle_id": c["id"], "planned_hours": 10}).status_code == 200
        r = client.delete(f"/api/cycles/{c['id']}")
        assert r.status_code == 409
        assert "plano" in r.json()["detail"].lower()
        assert "1" in r.json()["detail"]
        # plan data is untouched
        assert len(client.get(f"/api/projects/{p['id']}/plans").json()) == 1

    def test_delete_cycle_without_plans_ok(self, client):
        c = _cycle(client)
        assert client.delete(f"/api/cycles/{c['id']}").status_code == 204

    def test_delete_user_with_dependents_ok(self, client, db_session):
        u = User(username="dep", hashed_password=hash_password("secret1"), role="user")
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        assert client.delete(f"/api/users/{u.id}").status_code == 204

    def test_delete_rate_card_ok(self, client, db_session):
        sl = _level(db_session)
        r = client.post("/api/rate-cards", json={"seniority_level_id": sl.id, "hourly_rate": 10,
                                                 "valid_from": "2026-01-01"})
        assert client.delete(f"/api/rate-cards/{r.json()['id']}").status_code == 204


# ---------------------------------------------------------------------------
# C2 — plan CSV import
# ---------------------------------------------------------------------------

class TestC2PlanImport:
    def _setup(self, client):
        _cycle(client, "C1", "2026-01-01", "2026-01-31")
        _cycle(client, "C2", "2026-02-01", "2026-02-28")
        _project(client, "P-1")

    def test_nan_and_inf_rejected_per_row(self, client):
        self._setup(client)
        text = ("pep_wbs,cycle_name,planned_hours,planned_cost\n"
                "P-1,C1,nan,\n"
                "P-1,C2,inf,\n"
                "P-1,C2,10,nan\n"
                "P-1,C2,10,5\n")
        r = _csv(client, "/api/projects/plans/import", text)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["created"] == 1
        assert len(d["errors"]) == 3

    def test_duplicate_rows_keep_first(self, client):
        self._setup(client)
        text = ("pep_wbs,cycle_name,planned_hours\n"
                "P-1,C1,10\n"
                "P-1,C1,99\n"
                "P-1,C2,20\n")
        r = _csv(client, "/api/projects/plans/import", text)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["created"] == 2
        assert len(d["errors"]) == 1 and "duplic" in d["errors"][0].lower()
        pid = client.get("/api/projects").json()[0]["id"]
        hours = sorted(p["planned_hours"] for p in client.get(f"/api/projects/{pid}/plans").json())
        assert hours == [10.0, 20.0]

    def test_header_only_returns_message(self, client):
        self._setup(client)
        r = _csv(client, "/api/projects/plans/import", "pep_wbs,cycle_name,planned_hours\n")
        assert r.status_code == 200
        d = r.json()
        assert d["created"] == 0 and d["updated"] == 0
        assert d["message"]

    def test_summary_message(self, client):
        self._setup(client)
        r = _csv(client, "/api/projects/plans/import",
                 "pep_wbs,cycle_name,planned_hours\nP-1,C1,5\n")
        assert "1 criado" in r.json()["message"]


# ---------------------------------------------------------------------------
# C3 — bcrypt 72 byte limit
# ---------------------------------------------------------------------------

class TestC3LongPasswords:
    def test_create_user_long_password_422(self, client):
        r = client.post("/api/users", json={"username": "longpw", "password": "a" * 73})
        assert r.status_code == 422
        assert "72" in r.text

    def test_create_user_multibyte_over_72_bytes_422(self, client):
        r = client.post("/api/users", json={"username": "mbpw", "password": "é" * 37})
        assert r.status_code == 422

    def test_create_user_exactly_72_bytes_ok_and_login(self, client):
        pw = "a" * 72
        assert client.post("/api/users", json={"username": "ok72", "password": pw}).status_code == 201
        assert client.post("/api/token", data={"username": "ok72", "password": pw}).status_code == 200

    def test_change_password_long_422(self, client, db_session):
        u = User(username="chg", hashed_password=hash_password("secret1"), role="user")
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        r = client.patch(f"/api/users/{u.id}/password", json={"new_password": "b" * 100})
        assert r.status_code == 422

    def test_login_with_very_long_password_is_401(self, client, db_session):
        u = User(username="loginlong", hashed_password=hash_password("secret1"), role="user")
        db_session.add(u)
        db_session.commit()
        r = client.post("/api/token", data={"username": "loginlong", "password": "x" * 500})
        assert r.status_code == 401

    def test_verify_password_never_raises(self):
        h = hash_password("secret1")
        assert verify_password("x" * 500, h) is False
        assert verify_password("a\x00b", h) is False
        assert verify_password("secret1", "not-a-hash") is False

    def test_nul_byte_password_422(self, client):
        r = client.post("/api/users", json={"username": "nulpw", "password": "abc\x00def"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# C4 — rate card update with unknown level
# ---------------------------------------------------------------------------

class TestC4:
    def test_put_rate_card_unknown_level_404(self, client, db_session):
        sl = _level(db_session)
        rid = client.post("/api/rate-cards", json={"seniority_level_id": sl.id, "hourly_rate": 10,
                                                   "valid_from": "2026-01-01"}).json()["id"]
        r = client.put(f"/api/rate-cards/{rid}", json={"seniority_level_id": 99999, "hourly_rate": 10,
                                                       "valid_from": "2026-01-01"})
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# C5 / C9 — validation rules
# ---------------------------------------------------------------------------

def _rule(**kw):
    base = {"field": "horas_individuais", "operator": "gt", "value": "10",
            "action": "warning", "order": 20, "is_active": True}
    base.update(kw)
    return base


class TestC5RuleOrder:
    def test_post_huge_order_422(self, client):
        assert client.post("/api/validation-rules", json=_rule(order=99999999999999999999)).status_code == 422

    def test_post_order_above_max_422(self, client):
        assert client.post("/api/validation-rules", json=_rule(order=10001)).status_code == 422

    def test_put_huge_order_422(self, client):
        rid = client.post("/api/validation-rules", json=_rule()).json()["id"]
        assert client.put(f"/api/validation-rules/{rid}",
                          json=_rule(order=99999999999999999999)).status_code == 422

    def test_reorder_huge_422(self, client):
        rid = client.post("/api/validation-rules", json=_rule()).json()["id"]
        assert client.post("/api/validation-rules/reorder", json={rid: 99999999999999999999}).status_code == 422

    def test_reorder_valid(self, client):
        rid = client.post("/api/validation-rules", json=_rule()).json()["id"]
        assert client.post("/api/validation-rules/reorder", json={rid: 77}).status_code == 200


class TestC9RuleVocabulary:
    def test_unknown_operator_422(self, client):
        assert client.post("/api/validation-rules", json=_rule(operator="banana")).status_code == 422

    def test_unknown_action_422(self, client):
        assert client.post("/api/validation-rules", json=_rule(action="explode")).status_code == 422

    def test_english_quarantine_action_422(self, client):
        assert client.post("/api/validation-rules", json=_rule(action="quarantine")).status_code == 422

    @pytest.mark.parametrize("action", ["info", "warning", "quarentena", "descarte"])
    def test_valid_actions(self, client, action):
        assert client.post("/api/validation-rules", json=_rule(action=action)).status_code == 201

    @pytest.mark.parametrize("op", ["gt", "gte", "lt", "lte"])
    def test_numeric_operators_need_numeric_value(self, client, op):
        assert client.post("/api/validation-rules", json=_rule(operator=op, value="abc")).status_code == 422
        assert client.post("/api/validation-rules", json=_rule(operator=op, value=None)).status_code == 422
        assert client.post("/api/validation-rules", json=_rule(operator=op, value="nan")).status_code == 422
        assert client.post("/api/validation-rules", json=_rule(operator=op, value="8.5")).status_code == 201

    @pytest.mark.parametrize("op", ["eq", "neq", "contem", "nao_contem", "in_lista"])
    def test_value_operators_need_non_empty(self, client, op):
        assert client.post("/api/validation-rules", json=_rule(operator=op, value="  ")).status_code == 422
        assert client.post("/api/validation-rules", json=_rule(operator=op, value=None)).status_code == 422

    @pytest.mark.parametrize("op", ["vazio", "nao_vazio"])
    def test_empty_operators_need_no_value(self, client, op):
        r = client.post("/api/validation-rules",
                        json=_rule(field="pep_wbs", operator=op, value=None, action="info"))
        assert r.status_code == 201

    def test_system_rule_cannot_become_inert(self, client, db_session):
        sys_rule = db_session.query(ValidationRule).filter_by(is_system=True, operator="gt").first()
        body = {"field": sys_rule.field, "operator": sys_rule.operator, "action": sys_rule.action,
                "order": sys_rule.order, "is_active": True, "value": None}
        assert client.put(f"/api/validation-rules/{sys_rule.id}", json=body).status_code == 422
        body["value"] = "abc"
        assert client.put(f"/api/validation-rules/{sys_rule.id}", json=body).status_code == 422
        body["value"] = "30"
        assert client.put(f"/api/validation-rules/{sys_rule.id}", json=body).status_code == 200


# ---------------------------------------------------------------------------
# C6 — cycle CSV import
# ---------------------------------------------------------------------------

class TestC6CycleImport:
    def test_bad_row_does_not_discard_valid_rows(self, client):
        text = ("name,start_date,end_date\n"
                "A,2026-01-01,2026-01-31\n"
                "B,not-a-date,2026-02-28\n"
                "C,2026-03-01,2026-03-31\n")
        r = _csv(client, "/api/cycles/import", text)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["created"] == 2
        assert len(d["errors"]) == 1 and "Linha 3" in d["errors"][0]
        assert sorted(c["name"] for c in client.get("/api/cycles").json()) == ["A", "C"]

    def test_day_first_dates(self, client):
        text = "name,start_date,end_date\nD,01/04/2030,30/04/2030\n"
        r = _csv(client, "/api/cycles/import", text)
        assert r.json()["created"] == 1
        c = client.get("/api/cycles").json()[0]
        assert c["start_date"] == "2030-04-01" and c["end_date"] == "2030-04-30"

    def test_iso_dates_still_work(self, client):
        r = _csv(client, "/api/cycles/import", "name,start_date,end_date\nE,2030-05-01,2030-05-31\n")
        assert r.json()["created"] == 1

    def test_duplicate_name_case_insensitive_not_created(self, client):
        _cycle(client, "Jan/2026")
        r = _csv(client, "/api/cycles/import", "name,start_date,end_date\njan/2026,2027-01-01,2027-01-31\n")
        assert r.json()["created"] == 0


# ---------------------------------------------------------------------------
# C7 — rate card import
# ---------------------------------------------------------------------------

class TestC7RateCardImport:
    def test_update_path_checks_overlap(self, client, db_session):
        sl = _level(db_session, "Sr")
        db_session.add_all([
            RateCard(seniority_level_id=sl.id, hourly_rate=10, valid_from=date(2026, 1, 1), valid_to=date(2026, 3, 31)),
            RateCard(seniority_level_id=sl.id, hourly_rate=12, valid_from=date(2026, 4, 1), valid_to=date(2026, 6, 30)),
        ])
        db_session.commit()
        text = "seniority_level,valid_from,valid_to,hourly_rate\nSr,2026-01-01,2026-05-31,11\n"
        r = _csv(client, "/api/rate-cards/import", text)
        assert r.status_code == 200
        d = r.json()
        assert d["updated"] == 0
        assert len(d["errors"]) == 1 and "sobrepos" in d["errors"][0].lower()
        card = db_session.query(RateCard).filter_by(valid_from=date(2026, 1, 1)).first()
        db_session.refresh(card)
        assert card.valid_to == date(2026, 3, 31)

    def test_update_without_overlap_ok(self, client, db_session):
        sl = _level(db_session, "Sr")
        db_session.add(RateCard(seniority_level_id=sl.id, hourly_rate=10, valid_from=date(2026, 1, 1)))
        db_session.commit()
        text = "seniority_level,valid_from,valid_to,hourly_rate\nSr,2026-01-01,2026-05-31,11\n"
        assert _csv(client, "/api/rate-cards/import", text).json()["updated"] == 1

    def test_invalid_row_message_is_short(self, client, db_session):
        text = "seniority_level,valid_from,valid_to,hourly_rate\nSr,2026-01-01,,-5\n"
        d = _csv(client, "/api/rate-cards/import", text).json()
        assert d["created"] == 0
        assert len(d["errors"]) == 1
        assert "\n" not in d["errors"][0] and len(d["errors"][0]) < 120

    def test_bad_rate_text_message_is_short(self, client):
        text = "seniority_level,valid_from,valid_to,hourly_rate\nSr,2026-01-01,,abc\n"
        d = _csv(client, "/api/rate-cards/import", text).json()
        assert len(d["errors"]) == 1 and "\n" not in d["errors"][0] and len(d["errors"][0]) < 120

    def test_nan_rate_rejected(self, client):
        text = "seniority_level,valid_from,valid_to,hourly_rate\nSr,2026-01-01,,nan\n"
        d = _csv(client, "/api/rate-cards/import", text).json()
        assert d["created"] == 0 and len(d["errors"]) == 1


# ---------------------------------------------------------------------------
# C8 — seniority delete with rate cards
# ---------------------------------------------------------------------------

class TestC8:
    def test_delete_level_with_rate_cards_409(self, client, db_session):
        sl = _level(db_session)
        db_session.add(RateCard(seniority_level_id=sl.id, hourly_rate=10, valid_from=date(2026, 1, 1)))
        db_session.commit()
        r = client.delete(f"/api/seniority-levels/{sl.id}")
        assert r.status_code == 409
        assert "1" in r.json()["detail"] and "rate" in r.json()["detail"].lower()
        assert db_session.query(RateCard).count() == 1

    def test_delete_level_without_cards_ok(self, client, db_session):
        sl = _level(db_session)
        assert client.delete(f"/api/seniority-levels/{sl.id}").status_code == 204


# ---------------------------------------------------------------------------
# C11 — global config
# ---------------------------------------------------------------------------

def _cfg(**kw):
    base = {"extra_hours_multiplier": 1.5, "standby_hours_multiplier": 0.33}
    base.update(kw)
    return base


class TestC11Config:
    def test_unknown_timezone_422(self, client):
        assert client.put("/api/config", json=_cfg(timezone="Mars/Olympus")).status_code == 422

    def test_valid_timezone_ok(self, client):
        assert client.put("/api/config", json=_cfg(timezone="UTC")).status_code == 200

    def test_warning_must_be_below_critical(self, client):
        r = client.put("/api/config", json=_cfg(budget_warning_threshold=1.0, budget_critical_threshold=1.0))
        assert r.status_code == 422
        r = client.put("/api/config", json=_cfg(budget_warning_threshold=0.95, budget_critical_threshold=0.9))
        assert r.status_code == 422

    def test_threshold_bounds(self, client):
        assert client.put("/api/config", json=_cfg(budget_critical_threshold=5.5)).status_code == 422
        assert client.put("/api/config", json=_cfg(budget_warning_threshold=0)).status_code == 422
        assert client.put("/api/config", json=_cfg(budget_warning_threshold=0.8,
                                                   budget_critical_threshold=5)).status_code == 200

    def test_multiplier_bounds(self, client):
        assert client.put("/api/config", json=_cfg(extra_hours_multiplier=10.5)).status_code == 422
        assert client.put("/api/config", json=_cfg(standby_hours_multiplier=11)).status_code == 422
        assert client.put("/api/config", json=_cfg(extra_hours_multiplier=10)).status_code == 200

    def test_anomaly_bounds(self, client):
        assert client.put("/api/config", json=_cfg(anomaly_max_daily_hours=25)).status_code == 422
        assert client.put("/api/config", json=_cfg(anomaly_max_daily_hours=0)).status_code == 422
        assert client.put("/api/config", json=_cfg(anomaly_max_daily_hours=24)).status_code == 200

    def test_non_finite_rejected(self, client):
        r = client.put("/api/config", content='{"extra_hours_multiplier": NaN, "standby_hours_multiplier": 1}',
                       headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        r = client.put("/api/config", content='{"extra_hours_multiplier": 1, "standby_hours_multiplier": Infinity}',
                       headers={"Content-Type": "application/json"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# C12 — projects
# ---------------------------------------------------------------------------

def _add_record(db, pep, cycle):
    c = Collaborator(name="Ana")
    db.add(c)
    db.commit()
    db.add(TimesheetRecord(collaborator_id=c.id, cycle_id=cycle.id, record_date=date(2026, 1, 15),
                           pep_wbs=pep, pep_description="x", normal_hours=8.0, extra_hours=0.0,
                           standby_hours=0.0))
    db.commit()


class TestC12Projects:
    def test_planned_end_before_start_422(self, client):
        r = client.post("/api/projects", json={"pep_wbs": "X", "start_date": "2026-05-01",
                                               "planned_end_date": "2026-04-01"})
        assert r.status_code == 422

    def test_completion_before_start_422(self, client):
        r = client.post("/api/projects", json={"pep_wbs": "X", "start_date": "2026-05-01",
                                               "completion_date": "2026-04-01"})
        assert r.status_code == 422

    def test_update_dates_validated(self, client):
        p = _project(client, "X")
        r = client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "X", "start_date": "2026-05-01",
                                                         "planned_end_date": "2026-04-01"})
        assert r.status_code == 422

    def test_inf_budget_rejected(self, client):
        r = client.post("/api/projects", content='{"pep_wbs": "X", "budget_hours": Infinity}',
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422
        r = client.post("/api/projects", content='{"pep_wbs": "X", "budget_cost": NaN}',
                        headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_negative_budget_rejected(self, client):
        assert client.post("/api/projects", json={"pep_wbs": "X", "budget_hours": -1}).status_code == 422

    def test_rename_with_records_409(self, client, db_session, sample_cycle):
        p = _project(client, "OLD")
        _add_record(db_session, "OLD", sample_cycle)
        r = client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "NEW"})
        assert r.status_code == 409
        assert client.get("/api/projects").json()[0]["pep_wbs"] == "OLD"

    def test_rename_with_summary_rows_409(self, client, db_session, sample_cycle):
        from backend.app.models import PepCycleSummary
        p = _project(client, "OLD")
        cols = {c.name for c in PepCycleSummary.__table__.columns}
        kw = {"pep_wbs": "OLD", "cycle_id": sample_cycle.id}
        for k in ("total_hours", "total_cost", "normal_hours", "extra_hours", "standby_hours", "record_count"):
            if k in cols:
                kw[k] = 0
        db_session.add(PepCycleSummary(**kw))
        db_session.commit()
        assert client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "NEW"}).status_code == 409

    def test_rename_without_history_ok(self, client):
        p = _project(client, "OLD")
        r = client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "NEW"})
        assert r.status_code == 200 and r.json()["pep_wbs"] == "NEW"

    def test_update_same_pep_with_records_ok(self, client, db_session, sample_cycle):
        p = _project(client, "KEEP")
        _add_record(db_session, "KEEP", sample_cycle)
        assert client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "KEEP", "name": "n"}).status_code == 200

    def test_delete_with_records_409(self, client, db_session, sample_cycle):
        p = _project(client, "DEL")
        _add_record(db_session, "DEL", sample_cycle)
        r = client.delete(f"/api/projects/{p['id']}")
        assert r.status_code == 409
        assert "registro" in r.json()["detail"].lower()
        assert len(client.get("/api/projects").json()) == 1

    def test_delete_without_records_ok(self, client):
        p = _project(client, "DEL2")
        assert client.delete(f"/api/projects/{p['id']}").status_code == 204

    def test_ativo_plus_completion_becomes_encerrado_on_create(self, client):
        p = _project(client, "S1", status="ativo", completion_date="2026-03-01")
        assert p["status"] == "encerrado"

    def test_ativo_plus_completion_becomes_encerrado_on_update(self, client):
        p = _project(client, "S2")
        r = client.put(f"/api/projects/{p['id']}", json={"pep_wbs": "S2", "status": "ativo",
                                                         "completion_date": "2026-03-01"})
        assert r.json()["status"] == "encerrado"
        assert client.get("/api/projects").json()[0]["status"] == "encerrado"


# ---------------------------------------------------------------------------
# C13 — cycle update rules
# ---------------------------------------------------------------------------

class TestC13Cycles:
    def test_closed_cycle_cannot_be_edited(self, client):
        c = _cycle(client)
        client.patch(f"/api/cycles/{c['id']}/toggle-status")
        r = client.put(f"/api/cycles/{c['id']}", json={"name": "Novo", "start_date": "2026-01-01",
                                                       "end_date": "2026-01-31"})
        assert r.status_code == 409

    def test_reopen_via_toggle_still_works(self, client):
        c = _cycle(client)
        client.patch(f"/api/cycles/{c['id']}/toggle-status")
        r = client.patch(f"/api/cycles/{c['id']}/toggle-status")
        assert r.status_code == 200 and r.json()["is_closed"] is False

    def test_dates_cannot_exclude_existing_records(self, client, db_session, sample_cycle, sample_record):
        r = client.put(f"/api/cycles/{sample_cycle.id}",
                       json={"name": sample_cycle.name, "start_date": "2026-01-20", "end_date": "2026-01-31"})
        assert r.status_code == 409

    def test_dates_covering_records_ok(self, client, db_session, sample_cycle, sample_record):
        r = client.put(f"/api/cycles/{sample_cycle.id}",
                       json={"name": sample_cycle.name, "start_date": "2026-01-10", "end_date": "2026-01-31"})
        assert r.status_code == 200

    def test_rename_cycle_with_records_ok(self, client, sample_cycle, sample_record):
        r = client.put(f"/api/cycles/{sample_cycle.id}",
                       json={"name": "Renomeado", "start_date": "2026-01-01", "end_date": "2026-01-31"})
        assert r.status_code == 200

    def test_duplicate_name_case_insensitive_create(self, client):
        _cycle(client, "Jan/2026")
        r = client.post("/api/cycles", json={"name": "  jan/2026 ", "start_date": "2027-01-01",
                                             "end_date": "2027-01-31"})
        assert r.status_code == 409

    def test_duplicate_name_on_update(self, client):
        _cycle(client, "A", "2026-01-01", "2026-01-31")
        b = _cycle(client, "B", "2026-02-01", "2026-02-28")
        r = client.put(f"/api/cycles/{b['id']}", json={"name": "a", "start_date": "2026-02-01",
                                                       "end_date": "2026-02-28"})
        assert r.status_code == 409

    def test_update_own_name_different_case_ok(self, client):
        a = _cycle(client, "A", "2026-01-01", "2026-01-31")
        r = client.put(f"/api/cycles/{a['id']}", json={"name": "a", "start_date": "2026-01-01",
                                                       "end_date": "2026-01-31"})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# C14 — whitespace / blank names / case-insensitive usernames
# ---------------------------------------------------------------------------

class TestC14Names:
    def test_cycle_blank_name_422(self, client):
        r = client.post("/api/cycles", json={"name": "   ", "start_date": "2026-01-01", "end_date": "2026-01-31"})
        assert r.status_code == 422

    def test_cycle_name_stripped(self, client):
        c = _cycle(client, "  Padded  ")
        assert c["name"] == "Padded"

    def test_seniority_blank_and_stripped(self, client):
        assert client.post("/api/seniority-levels", json={"name": "  "}).status_code == 422
        r = client.post("/api/seniority-levels", json={"name": "  Jr  "})
        assert r.status_code == 201 and r.json()["name"] == "Jr"

    def test_project_blank_pep_422_and_trimmed(self, client):
        assert client.post("/api/projects", json={"pep_wbs": "  "}).status_code == 422
        p = _project(client, "  60IT-1  ", name="  Nome  ")
        assert p["pep_wbs"] == "60IT-1" and p["name"] == "Nome"

    def test_project_blank_name_becomes_none(self, client):
        p = _project(client, "NB", name="   ")
        assert p["name"] is None

    def test_username_blank_and_trimmed(self, client):
        assert client.post("/api/users", json={"username": "     ", "password": "secret1"}).status_code == 422
        r = client.post("/api/users", json={"username": "  carol  ", "password": "secret1"})
        assert r.status_code == 201 and r.json()["username"] == "carol"

    def test_username_unique_ignoring_case(self, client):
        assert client.post("/api/users", json={"username": "bob", "password": "secret1"}).status_code == 201
        r = client.post("/api/users", json={"username": "BOB", "password": "secret1"})
        assert r.status_code in (400, 409)

    def test_login_case_insensitive_when_unambiguous(self, client):
        client.post("/api/users", json={"username": "dave", "password": "secret1"})
        r = client.post("/api/token", data={"username": "DAVE", "password": "secret1"})
        assert r.status_code == 200
        r = client.post("/api/token", data={"username": "dave", "password": "secret1"})
        assert r.status_code == 200

    def test_login_ambiguous_requires_exact(self, client, db_session):
        for n in ("Al", "AL"):
            db_session.add(User(username=n, hashed_password=hash_password("secret1"), role="user"))
        db_session.commit()
        assert client.post("/api/token", data={"username": "Al", "password": "secret1"}).status_code == 200
        assert client.post("/api/token", data={"username": "aL", "password": "secret1"}).status_code == 401

    def test_preset_name_blank_422(self, client):
        assert client.post("/api/theme/presets", json={"name": "   ", "config": {}}).status_code == 422


# ---------------------------------------------------------------------------
# C15 — pagination / dates
# ---------------------------------------------------------------------------

class TestC15:
    def test_audit_limit_must_be_positive(self, client):
        assert client.get("/api/audit-log?limit=-1").status_code == 422
        assert client.get("/api/audit-log?limit=0").status_code == 422
        assert client.get("/api/audit-log?offset=-1").status_code == 422
        assert client.get("/api/audit-log?limit=5").status_code == 200

    def test_alerts_limit_and_offset(self, client):
        assert client.get("/api/project-alerts/?limit=-1").status_code == 422
        assert client.get("/api/project-alerts/?offset=-1").status_code == 422
        assert client.get("/api/project-alerts/?limit=5").status_code == 200

    def test_alerts_date_parsed(self, client):
        assert client.get("/api/project-alerts/?date_from=abc").status_code == 422
        assert client.get("/api/project-alerts/?date_to=2026-13-45").status_code == 422
        assert client.get("/api/project-alerts/?date_from=2026-01-01&date_to=2026-12-31").status_code == 200

    def test_alerts_date_filter_still_works(self, client, db_session):
        from datetime import datetime
        from backend.app.models import ProjectAlert
        p = Project(pep_wbs="AL-1")
        db_session.add(p)
        db_session.commit()
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs="AL-1", alert_type="budget_warning",
                                    level="warning", message="m", created_at=datetime(2026, 3, 10, 15, 0)))
        db_session.commit()
        ok = client.get("/api/project-alerts/?date_from=2026-03-10&date_to=2026-03-10").json()
        assert len(ok) == 1
        none = client.get("/api/project-alerts/?date_from=2026-03-11").json()
        assert none == []


# ---------------------------------------------------------------------------
# C16 — theme validation
# ---------------------------------------------------------------------------

class TestC16Theme:
    def test_color_must_be_hex(self, client):
        assert client.put("/api/theme", json={"color_primary": "red"}).status_code == 422
        assert client.put("/api/theme", json={"color_primary": "url(javascript:x)"}).status_code == 422
        assert client.put("/api/theme", json={"color_text": "#12"}).status_code == 422

    def test_short_hex_ok(self, client):
        assert client.put("/api/theme", json={"color_primary": "#abc"}).status_code == 200

    def test_app_name_limits(self, client):
        assert client.put("/api/theme", json={"app_name": "x" * 61}).status_code == 422
        assert client.put("/api/theme", json={"app_name": "   "}).status_code == 422
        assert client.put("/api/theme", json={"app_name": "x" * 60}).status_code == 200

    def test_font_family_safe(self, client):
        assert client.put("/api/theme", json={"font_family": "x; background:url(//evil)"}).status_code == 422
        assert client.put("/api/theme", json={"font_family": "a" * 200}).status_code == 422
        assert client.put("/api/theme", json={"font_family": "'Roboto', sans-serif"}).status_code == 200

    def test_density_and_radius(self, client):
        assert client.put("/api/theme", json={"density": "huge"}).status_code == 422
        assert client.put("/api/theme", json={"border_radius": "round"}).status_code == 422
        assert client.put("/api/theme", json={"border_radius": "rounded"}).status_code == 200

    def test_get_theme_survives_bad_stored_values(self, client, db_session):
        from backend.app.models import GlobalConfig
        db_session.add(GlobalConfig(id=1, ui_theme={"color_primary": "red", "app_name": "Ok"}))
        db_session.commit()
        r = client.get("/api/theme")
        assert r.status_code == 200
        assert r.json()["app_name"] == "Ok"
        assert r.json()["color_primary"].startswith("#")

    def test_preset_config_validated(self, client):
        good = {"color_primary": "#aabbcc", "density": "normal", "chart_palette": ["#aabbcc"]}
        assert client.post("/api/theme/presets", json={"name": "P1", "config": good}).status_code == 200
        for bad in (
            {"color_primary": "red"},
            {"density": "huge"},
            {"border_radius": "x"},
            {"chart_palette": ["#fff", "nothex"]},
            {"chart_palette": ["#aabbcc"] * 9},
            {"app_name": "x" * 100},
            {"font_family": "a;b"},
        ):
            r = client.post("/api/theme/presets", json={"name": "Bad", "config": bad})
            assert r.status_code == 422, bad

    def test_preset_config_must_be_dict(self, client):
        assert client.post("/api/theme/presets", json={"name": "L", "config": []}).status_code == 422

    def test_preset_import_invalid_rows_reported(self, client):
        header = ("name,is_builtin,color_primary,color_background,color_surface,color_accent,color_success,"
                  "color_warning,color_danger,color_text,color_text_muted,density,pal_0,pal_1\r\n")
        ok = "Good,false,#001122,#000000,#111111,#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,#888888,normal,#112233,#445566\r\n"
        bad_density = "BadDens,false,#001122,#000000,#111111,#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,#888888,huge,,\r\n"
        bad_pal = "BadPal,false,#001122,#000000,#111111,#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,#888888,normal,zzz,\r\n"
        bad_color = "BadCol,false,#00112,#000000,#111111,#ff00ff,#00ff00,#ffff00,#ff0000,#ffffff,#888888,normal,,\r\n"
        d = _csv(client, "/api/theme/presets/import", header + ok + bad_density + bad_pal + bad_color).json()
        assert d["created"] == 1
        assert len(d["errors"]) == 3
        assert d["skipped"] == 3
        names = [p["name"] for p in client.get("/api/theme/presets").json()]
        assert names == ["Good"]

    def test_logo_empty_file_rejected(self, client):
        client.get("/api/theme")
        r = client.post("/api/theme/logo", files={"file": ("logo.png", io.BytesIO(b""), "image/png")})
        assert r.status_code == 400

    def test_logo_bad_extension_rejected(self, client):
        client.get("/api/theme")
        r = client.post("/api/theme/logo", files={"file": ("logo.exe", io.BytesIO(b"abc"), "image/png")})
        assert r.status_code == 400

    def test_logo_bad_content_type_rejected(self, client):
        client.get("/api/theme")
        r = client.post("/api/theme/logo", files={"file": ("logo.png", io.BytesIO(b"abc"), "text/html")})
        assert r.status_code == 400

    def test_logo_without_config_row_does_not_500(self, client):
        r = client.post("/api/theme/logo", files={"file": ("logo.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")})
        assert r.status_code == 200
        client.delete("/api/theme/logo")


# ---------------------------------------------------------------------------
# C17 — plan upsert path/body mismatch
# ---------------------------------------------------------------------------

class TestC17:
    def test_body_cycle_mismatch_422(self, client):
        c1 = _cycle(client, "C1", "2026-01-01", "2026-01-31")
        c2 = _cycle(client, "C2", "2026-02-01", "2026-02-28")
        p = _project(client)
        r = client.put(f"/api/projects/{p['id']}/plans/{c1['id']}",
                       json={"cycle_id": c2["id"], "planned_hours": 5})
        assert r.status_code == 422

    def test_matching_ok(self, client):
        c1 = _cycle(client)
        p = _project(client)
        r = client.put(f"/api/projects/{p['id']}/plans/{c1['id']}",
                       json={"cycle_id": c1["id"], "planned_hours": 5})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# C18 — error handlers
# ---------------------------------------------------------------------------

class TestC18Handlers:
    def test_unhandled_exception_is_problem_json(self, client, monkeypatch):
        from backend.app.main import app
        import backend.app.routers.cycles as cyc

        def boom(db):
            raise RuntimeError("segredo interno /etc/passwd")

        monkeypatch.setattr(cyc, "_cycle_record_counts", boom)
        with TestClient(app, raise_server_exceptions=False) as c:
            r = c.get("/api/cycles")
        assert r.status_code == 500
        assert r.headers["content-type"].startswith("application/problem+json")
        body = r.json()
        assert body["status"] == 500 and body["title"] and body["detail"]
        assert "passwd" not in r.text and "Traceback" not in r.text
        assert body["type"]

    def test_validation_error_translated_with_field(self, client):
        r = client.post("/api/cycles", json={"start_date": "2026-01-01", "end_date": "2026-01-31"})
        assert r.status_code == 422
        d = r.json()["detail"]
        assert isinstance(d, str)
        assert "name" in d and "obrigatório" in d.lower()

    def test_validation_string_too_short(self, client):
        r = client.post("/api/users", json={"username": "ab", "password": "secret1"})
        assert r.status_code == 422
        d = r.json()["detail"]
        assert "username" in d and "caracteres" in d

    def test_validation_greater_than(self, client):
        r = client.put("/api/config", json={"extra_hours_multiplier": 0, "standby_hours_multiplier": 1})
        assert "extra_hours_multiplier" in r.json()["detail"] and "maior" in r.json()["detail"]

    def test_value_error_prefix_removed(self, client):
        r = client.post("/api/users", json={"username": "okname", "password": "a" * 80})
        d = r.json()["detail"]
        assert "Value error" not in d and "72" in d

    def test_errors_list_preserved(self, client):
        r = client.post("/api/cycles", json={})
        body = r.json()
        assert isinstance(body["errors"], list) and body["errors"][0]["loc"]

    def test_handler_serializes_bytes_and_ctx(self):
        from fastapi.exceptions import RequestValidationError
        from backend.app.main import _validation_exception_handler

        exc = RequestValidationError([
            {"type": "value_error", "loc": ("body", "a"), "msg": "Value error, ruim",
             "input": b"\xff\xfe", "ctx": {"error": ValueError("boom")}},
            {"type": "some_new_type", "loc": ("query", "q"), "msg": "Original text", "input": object()},
        ])
        resp = asyncio.run(_validation_exception_handler(None, exc))
        assert resp.status_code == 422
        import json
        body = json.loads(resp.body)
        assert "ruim" in body["detail"] and "Original text" in body["detail"]

    def test_huge_path_id_is_404_not_500(self, client):
        from backend.app.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            assert c.delete("/api/cycles/99999999999999999999").status_code == 404
            assert c.delete("/api/projects/99999999999999999999").status_code == 404

    def test_invalid_json_body_ok(self, client):
        r = client.post("/api/cycles", content=b"\xff\xfe", headers={"Content-Type": "application/json"})
        assert r.status_code in (400, 422)


# ---------------------------------------------------------------------------
# C19 — migration failures are loud
# ---------------------------------------------------------------------------

class TestC19Migrations:
    def test_migration_failure_logged_at_error(self, monkeypatch, caplog):
        import logging
        from backend.app import database

        class _BadEngine:
            def begin(self):
                raise RuntimeError("falha de schema")

        monkeypatch.setattr(database, "engine", _BadEngine())
        with caplog.at_level(logging.ERROR, logger="backend.app.database"):
            with pytest.raises(RuntimeError):
                database._migrate_columns()
        recs = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert recs and recs[0].exc_info
