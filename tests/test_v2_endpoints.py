"""Tests for v2 consolidated endpoints.

Covers: /api/v2/filters, /api/v2/portfolio, /api/v2/effort,
        /api/v2/trends, /api/v2/forecast, and services/evm.py unit tests.

Auth is handled by the session-level `client` fixture in conftest.py
(dependency_overrides[get_current_user] = lambda: _MOCK_ADMIN).
Data setup uses `db_session` to write to the shared in-memory DB.
"""
from __future__ import annotations

from datetime import date

import pytest

from backend.app.models import (
    Collaborator, Cycle, Project, RateCard, SeniorityLevel, TimesheetRecord,
)


def _make_cycle(db, name, start, end):
    c = Cycle(name=name, start_date=start, end_date=end)
    db.add(c)
    db.flush()
    return c


def _make_project(db, pep, name, budget_hours=None, budget_cost=None):
    p = Project(pep_wbs=pep, name=name, budget_hours=budget_hours, budget_cost=budget_cost)
    db.add(p)
    db.flush()
    return p


def _make_collab(db, name, rate=50.0):
    sl = SeniorityLevel(name=f"SL-{name}")
    db.add(sl)
    db.flush()
    collab = Collaborator(name=name, seniority_level_id=sl.id)
    db.add(collab)
    db.flush()
    rc = RateCard(seniority_level_id=sl.id, hourly_rate=rate, valid_from=date(2024, 1, 1))
    db.add(rc)
    db.flush()
    return collab


def _make_record(db, collab, cycle, pep, pep_desc, normal_h, extra_h=0.0, standby_h=0.0,
                 rate=50.0, em=1.5, sm=0.33):
    nc = normal_h * rate
    ec = extra_h  * rate * em
    sc = standby_h * rate * sm
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=cycle.start_date,
        pep_wbs=pep,
        pep_description=pep_desc,
        normal_hours=normal_h,
        extra_hours=extra_h,
        standby_hours=standby_h,
        cost_per_hour=rate,
        normal_cost=nc,
        extra_cost=ec,
        standby_cost=sc,
    )
    db.add(r)
    db.flush()
    return r


# ── /api/v2/filters ──────────────────────────────────────────────────────────

class TestFilters:
    def test_returns_three_keys(self, client, clean_db):
        r = client.get("/api/v2/filters")
        assert r.status_code == 200
        body = r.json()
        assert "collaborators" in body
        assert "peps" in body
        assert "cycles" in body

    def test_includes_collaborator_and_pep_after_seed(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Ana Silva")
        _make_record(db_session, collab, c, "60IT-001-01", "Sistema Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/filters")
        body = r.json()
        assert any(x["name"] == "Ana Silva" for x in body["collaborators"])
        assert any(x["code"] == "60IT-001-01" for x in body["peps"])
        assert any(x["name"] == "JAN/2025" for x in body["cycles"])


# ── /api/v2/portfolio ────────────────────────────────────────────────────────

class TestPortfolio:
    def test_empty_returns_list(self, client, clean_db):
        r = client.get("/api/v2/portfolio")
        assert r.status_code == 200
        assert r.json() == []

    def test_render_ready_fields_present(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Sistema Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/portfolio")
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        item = items[0]
        for field in ("cpi", "cpi_label", "cpi_color",
                      "health_hours", "health_cost",
                      "health_hours_color", "health_cost_color"):
            assert field in item, f"Missing field: {field}"

    def test_health_no_budget(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        collab = _make_collab(db_session, "Carlos", rate=0.0)
        _make_record(db_session, collab, c, "NO-BUDGET-01", "Sem orçamento", 10.0, rate=0.0)
        db_session.commit()

        r = client.get("/api/v2/portfolio")
        items = r.json()
        no_bgt = next((i for i in items if i["pep_wbs"] == "NO-BUDGET-01"), None)
        assert no_bgt is not None
        assert no_bgt["health_hours"] == "no_budget"
        assert no_bgt["cpi"] is None

    def test_cpi_under_budget(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana")
        # 8h normal + 2h extra → cost = 400 + 150 = 550; budget_cost=5000 → CPI ≫ 1
        _make_record(db_session, collab, c, "60IT-001-01", "Sistema Alpha", 8.0, extra_h=2.0)
        db_session.commit()

        r = client.get("/api/v2/portfolio")
        items = r.json()
        item = next(i for i in items if i["pep_wbs"] == "60IT-001-01")
        assert item["cpi"] is not None
        assert item["cpi"] > 1.0
        assert item["cpi_label"] == "Dentro do orçamento"
        assert item["cpi_color"] == "success"

    def test_cost_breakdown_fields(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Pedro")
        _make_record(db_session, collab, c, "60IT-002-01", "Sistema Beta",
                     normal_h=5.0, extra_h=2.0, standby_h=1.0)
        db_session.commit()

        r = client.get("/api/v2/portfolio")
        items = r.json()
        item = next(i for i in items if i["pep_wbs"] == "60IT-002-01")
        assert item["normal_cost"] == pytest.approx(250.0)   # 5 × 50
        assert item["extra_cost"]  == pytest.approx(150.0)   # 2 × 50 × 1.5
        assert item["standby_cost"] == pytest.approx(16.5)   # 1 × 50 × 0.33


# ── /api/v2/effort ───────────────────────────────────────────────────────────

class TestEffort:
    def test_empty_returns_list(self, client, clean_db):
        r = client.get("/api/v2/effort")
        assert r.status_code == 200
        assert r.json() == []

    def test_has_required_fields(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/effort")
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        item = items[0]
        for field in ("collaborator", "normal_hours", "extra_hours", "standby_hours", "total_hours"):
            assert field in item, f"Missing field: {field}"

    def test_totals_aggregated_correctly(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", normal_h=8.0)
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", normal_h=6.0, extra_h=2.0)
        db_session.commit()

        r = client.get("/api/v2/effort")
        items = r.json()
        ana = next(i for i in items if i["collaborator"] == "Ana")
        assert ana["normal_hours"] == pytest.approx(14.0)
        assert ana["extra_hours"]  == pytest.approx(2.0)
        assert ana["total_hours"]  == pytest.approx(16.0)


# ── /api/v2/trends ───────────────────────────────────────────────────────────

class TestTrends:
    def test_empty_returns_list(self, client, clean_db):
        r = client.get("/api/v2/trends")
        assert r.status_code == 200
        assert r.json() == []

    def test_has_delta_fields(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/trends")
        items = r.json()
        assert len(items) >= 1
        item = items[0]
        for field in ("hours_delta", "hours_delta_pct", "cost_delta", "cost_delta_pct"):
            assert field in item, f"Missing field: {field}"

    def test_first_cycle_delta_is_none(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/trends")
        first = r.json()[0]
        assert first["hours_delta"] is None
        assert first["hours_delta_pct"] is None

    def test_second_cycle_delta_computed(self, client, db_session, clean_db):
        c1 = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        c2 = _make_cycle(db_session, "FEV/2025", date(2025, 2, 1), date(2025, 2, 28))
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c1, "60IT-001-01", "Alpha", 16.0)
        _make_record(db_session, collab, c2, "60IT-001-01", "Alpha", 20.0)
        db_session.commit()

        r = client.get("/api/v2/trends")
        items = r.json()
        assert len(items) == 2
        second = items[1]
        # 20 - 16 = +4h
        assert second["hours_delta"] == pytest.approx(4.0)
        # 4/16 × 100 = 25%
        assert second["hours_delta_pct"] == pytest.approx(25.0)


# ── /api/v2/forecast ─────────────────────────────────────────────────────────

class TestForecast:
    def test_404_when_no_data(self, client, clean_db):
        r = client.get("/api/v2/forecast?pep_wbs=NONEXISTENT")
        assert r.status_code == 404

    def test_render_ready_fields_present(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Sistema Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/forecast?pep_wbs=60IT-001-01")
        assert r.status_code == 200
        body = r.json()
        for field in ("cpi", "cpi_label", "cpi_color", "spi", "spi_label",
                      "eac", "vac", "cv", "tcpi", "history"):
            assert field in body, f"Missing field: {field}"

    def test_history_has_delta_and_sv_cv(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/forecast?pep_wbs=60IT-001-01")
        hist = r.json()["history"]
        assert len(hist) >= 1
        pt = hist[0]
        for field in ("period_hours_delta", "period_cost_delta", "sv", "sv_label", "cv", "cv_label"):
            assert field in pt, f"Missing field in history: {field}"

    def test_cpi_under_budget(self, client, db_session, clean_db):
        # budget_cost=5000, budget_hours=100 → blended_rate=50/h
        # actual rate=30/h → actual_cost=8×30=240, EV=min(8/100,1)×5000=400
        # CPI = EV/AC = 400/240 ≈ 1.67  (under budget → > 1)
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana", rate=30.0)
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0, rate=30.0)
        db_session.commit()

        r = client.get("/api/v2/forecast?pep_wbs=60IT-001-01")
        body = r.json()
        assert body["cpi"] is not None
        assert body["cpi"] > 1.0
        assert body["cpi_label"] == "Dentro do orçamento"

    def test_no_budget_yields_none_indicators(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "MAR/2025", date(2025, 3, 1), date(2025, 3, 31))
        collab = _make_collab(db_session, "Pedro", rate=0.0)
        _make_record(db_session, collab, c, "NO-BUDGET", None, 5.0, rate=0.0)
        db_session.commit()

        r = client.get("/api/v2/forecast?pep_wbs=NO-BUDGET")
        body = r.json()
        assert body["cpi"] is None
        assert body["eac"] is None
        assert body["spi"] is None

    def test_forecast_name_included(self, client, db_session, clean_db):
        c = _make_cycle(db_session, "JAN/2025", date(2025, 1, 1), date(2025, 1, 31))
        _make_project(db_session, "60IT-001-01", "Projeto Alpha", budget_hours=100.0, budget_cost=5000.0)
        collab = _make_collab(db_session, "Ana")
        _make_record(db_session, collab, c, "60IT-001-01", "Alpha", 8.0)
        db_session.commit()

        r = client.get("/api/v2/forecast?pep_wbs=60IT-001-01")
        assert r.json()["name"] == "Projeto Alpha"


# ── services/evm.py unit tests ───────────────────────────────────────────────

class TestEvmService:
    def test_freeze_costs_normal(self):
        from backend.app.services.evm import freeze_costs
        nc, ec, sc = freeze_costs(8.0, 2.0, 1.0, 50.0, 1.5, 0.33)
        assert nc == pytest.approx(400.0)
        assert ec == pytest.approx(150.0)
        assert sc == pytest.approx(16.5)

    def test_freeze_costs_zero_extra(self):
        from backend.app.services.evm import freeze_costs
        nc, ec, sc = freeze_costs(8.0, 0.0, 0.0, 50.0, 1.5, 0.33)
        assert nc == pytest.approx(400.0)
        assert ec == 0.0
        assert sc == 0.0

    def test_compute_cpi_normal(self):
        from backend.app.services.evm import compute_cpi
        assert compute_cpi(75000.0, 62025.0) == pytest.approx(1.2092, rel=1e-3)

    def test_compute_cpi_zero_actual(self):
        from backend.app.services.evm import compute_cpi
        assert compute_cpi(75000.0, 0.0) is None

    def test_compute_cpi_no_budget(self):
        from backend.app.services.evm import compute_cpi
        assert compute_cpi(None, 62025.0) is None

    def test_compute_sv_positive(self):
        from backend.app.services.evm import compute_sv
        assert compute_sv(120.0, 100.0) == pytest.approx(20.0)

    def test_compute_sv_negative(self):
        from backend.app.services.evm import compute_sv
        assert compute_sv(80.0, 100.0) == pytest.approx(-20.0)

    def test_compute_sv_no_planned(self):
        from backend.app.services.evm import compute_sv
        assert compute_sv(80.0, None) is None

    def test_compute_period_delta(self):
        from backend.app.services.evm import compute_period_delta
        assert compute_period_delta(20.0, 15.0) == pytest.approx(5.0)
        assert compute_period_delta(20.0, None) is None

    def test_compute_period_delta_pct(self):
        from backend.app.services.evm import compute_period_delta_pct
        assert compute_period_delta_pct(20.0, 15.0) == pytest.approx(33.33, rel=1e-2)
        assert compute_period_delta_pct(20.0, 0.0) is None
        assert compute_period_delta_pct(20.0, None) is None

    def test_classify_health_ok(self):
        from backend.app.services.evm import classify_health
        assert classify_health(80.0, 100.0) == "ok"

    def test_classify_health_warning(self):
        from backend.app.services.evm import classify_health
        assert classify_health(92.0, 100.0) == "warning"

    def test_classify_health_overrun(self):
        from backend.app.services.evm import classify_health
        assert classify_health(105.0, 100.0) == "overrun"

    def test_classify_health_no_budget(self):
        from backend.app.services.evm import classify_health
        assert classify_health(50.0, None) == "no_budget"
        assert classify_health(50.0, 0.0) == "no_budget"

    def test_compute_ev_cost(self):
        from backend.app.services.evm import compute_ev_cost
        ev = compute_ev_cost(50.0, 5000.0, 100.0)
        assert ev == pytest.approx(2500.0)

    def test_compute_ev_cost_no_budget(self):
        from backend.app.services.evm import compute_ev_cost
        assert compute_ev_cost(50.0, None, 100.0) is None
        assert compute_ev_cost(50.0, 5000.0, 0.0) is None

    def test_compute_eac(self):
        from backend.app.services.evm import compute_eac
        assert compute_eac(10000.0, 0.8) == pytest.approx(12500.0)
        assert compute_eac(None, 0.8) is None
        assert compute_eac(10000.0, 0.0) is None

    def test_compute_vac(self):
        from backend.app.services.evm import compute_vac
        assert compute_vac(10000.0, 12500.0) == pytest.approx(-2500.0)
        assert compute_vac(None, 12500.0) is None

    def test_compute_cv(self):
        from backend.app.services.evm import compute_cv
        assert compute_cv(8000.0, 6000.0) == pytest.approx(2000.0)   # under budget
        assert compute_cv(5000.0, 7000.0) == pytest.approx(-2000.0)  # over budget
        assert compute_cv(None, 6000.0) is None
