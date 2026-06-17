"""EVM calculation integrity tests.

Verifies that CPI, EAC, and SV are computed with the correct formulas and
produce consistent results across /api/v2/portfolio (runway),
/api/v2/trends, and /api/projects/{id}/forecast.

Canonical definitions used throughout:
  AC  = actual cost (Σ cost_per_hour × weighted hours)
  EV  = min(consumed_hours / budget_hours, 1.0) × budget_cost  ← capped at BAC
  CPI = EV / AC
  EAC = budget_cost / CPI  (= BAC / CPI)
  PV  = min(cumulative_planned_hours / budget_hours, 1.0) × budget_cost
  SPI = EV / PV
  SV  = EV − PV
"""
from __future__ import annotations

import math
from datetime import date

import pytest

from backend.app.models import (
    Collaborator, Cycle, GlobalConfig, Project, ProjectCyclePlan,
    SeniorityLevel, RateCard, TimesheetRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cycle(db, name, y, m):
    import calendar
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last))
    db.add(c); db.commit(); db.refresh(c)
    return c


def _project(db, pep, budget_hours, budget_cost, name="Proj"):
    p = Project(
        pep_wbs=pep, name=name,
        budget_hours=float(budget_hours),
        budget_cost=float(budget_cost),
        status="ativo",
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def _collab(db, name):
    c = Collaborator(name=name)
    db.add(c); db.commit(); db.refresh(c)
    return c


def _rec(db, cycle, collab, pep, desc, normal, extra=0.0, standby=0.0, day=10, cph=100.0, em=1.0, sm=1.0):
    r = TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep, pep_description=desc,
        normal_hours=float(normal), extra_hours=float(extra), standby_hours=float(standby),
        cost_per_hour=float(cph),
        normal_cost=round(float(normal) * cph, 4),
        extra_cost=round(float(extra) * cph * em, 4),
        standby_cost=round(float(standby) * cph * sm, 4),
    )
    db.add(r); db.commit()
    return r


def _plan(db, project_id, cycle_id, planned_hours):
    p = ProjectCyclePlan(
        project_id=project_id, cycle_id=cycle_id,
        planned_hours=float(planned_hours),
    )
    db.add(p); db.commit()
    return p


def _global_config(db, em=1.0, sm=1.0):
    cfg = GlobalConfig(
        id=1, extra_hours_multiplier=em, standby_hours_multiplier=sm,
        anomaly_max_daily_hours=24.0, timezone="UTC",
        budget_warning_threshold=0.9, budget_critical_threshold=1.0,
    )
    db.add(cfg); db.commit()
    return cfg


# ---------------------------------------------------------------------------
# Core CPI simulation
# ---------------------------------------------------------------------------

class TestCpiIntegrity:
    """
    Scenario
    --------
    budget_hours = 100
    budget_cost  = 10_000
    consumed     = 50 h (normal hours, cost_per_hour = 100 → AC = 5_000)

    Expected (with em=sm=1):
      EV  = (50/100) × 10_000 = 5_000
      AC  = 50 × 100          = 5_000
      CPI = EV/AC              = 1.000
    """

    PEP = "60IT-999-01"
    DESC = "EVM-Test"
    BH = 100.0
    BC = 10_000.0
    NORMAL = 50.0
    CPH = 100.0

    # EV=5000, AC=5000 → CPI=1.0
    _EV   = (NORMAL / BH) * BC      # 5_000
    _AC   = NORMAL * CPH             # 5_000
    _CPI  = _EV / _AC                # 1.000
    _EAC  = BC / _CPI                # 10_000

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy = _cycle(db, "Jan/2026", 2026, 1)
        co = _collab(db, "Alice")
        p  = _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy, co, self.PEP, self.DESC, normal=self.NORMAL, cph=self.CPH)
        return p, cy

    def test_portfolio_health_cpi(self, client, db_session):
        self._seed(db_session)
        resp = client.get("/api/v2/portfolio")
        assert resp.status_code == 200
        items = resp.json()
        item = next((i for i in items if i["pep_wbs"] == self.PEP), None)
        assert item is not None, "PEP not found in v2/portfolio"
        assert abs(item["total_hours"] - self.NORMAL) < 0.01
        assert abs(item["total_cost"]  - self._AC)    < 0.01

    def test_runway_cpi(self, client, db_session):
        """CPI from /api/v2/runway must use EV/AC, not BAC/AC."""
        self._seed(db_session)
        resp = client.get("/api/v2/runway")
        assert resp.status_code == 200
        items = resp.json()
        item = next((i for i in items if i["pep_wbs"] == self.PEP), None)
        assert item is not None, "PEP not found in portfolio-runway"
        assert item["cpi"] is not None, "CPI should not be None"
        assert abs(item["cpi"] - self._CPI) < 0.01, (
            f"Runway CPI={item['cpi']:.4f}, expected {self._CPI:.4f}. "
            "Likely using BAC/AC instead of EV/AC."
        )

    def test_forecast_cpi(self, client, db_session):
        """CPI from /api/v2/forecast must match runway CPI."""
        self._seed(db_session)
        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["cpi"] is not None, "Forecast CPI should not be None"
        assert abs(fc["cpi"] - self._CPI) < 0.01, (
            f"Forecast CPI={fc['cpi']:.4f}, expected {self._CPI:.4f}."
        )

    def test_cpi_consistency_runway_vs_forecast(self, client, db_session):
        """Runway and forecast must return the same CPI value."""
        self._seed(db_session)

        runway = client.get("/api/v2/runway").json()
        ritem  = next((i for i in runway if i["pep_wbs"] == self.PEP), None)

        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()

        assert ritem is not None
        assert ritem["cpi"] is not None
        assert fc["cpi"]   is not None
        assert abs(ritem["cpi"] - fc["cpi"]) < 0.001, (
            f"CPI mismatch: runway={ritem['cpi']}, forecast={fc['cpi']}"
        )


class TestCpiIntegrity_PartialCompletion:
    """
    Scenario: 25% consumed, cost_per_hour higher than plan → CPI < 1.
    budget_hours=100, budget_cost=10_000
    consumed=25h, cost_per_hour=200 → AC=5_000
    EV = (25/100)×10_000 = 2_500
    CPI = 2_500/5_000 = 0.500
    EAC = 10_000/0.5 = 20_000
    """

    PEP  = "60IT-888-01"
    DESC = "EVM-Partial"
    BH   = 100.0
    BC   = 10_000.0
    NORM = 25.0
    CPH  = 200.0

    _EV  = (NORM / BH) * BC   # 2_500
    _AC  = NORM * CPH          # 5_000
    _CPI = _EV / _AC           # 0.500

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy = _cycle(db, "Feb/2026", 2026, 2)
        co = _collab(db, "Bob")
        p  = _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy, co, self.PEP, self.DESC, normal=self.NORM, cph=self.CPH)
        return p, cy

    def test_runway_cpi_partial(self, client, db_session):
        self._seed(db_session)
        resp  = client.get("/api/v2/runway").json()
        item  = next((i for i in resp if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["cpi"] is not None
        assert abs(item["cpi"] - self._CPI) < 0.01, (
            f"Expected CPI={self._CPI:.3f}, got {item['cpi']}"
        )

    def test_forecast_eac(self, client, db_session):
        """EAC = budget_cost / CPI — should flag overrun when CPI<1."""
        self._seed(db_session)
        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()
        expected_eac = self.BC / self._CPI   # 20_000
        assert fc["eac"] is not None
        assert abs(fc["eac"] - expected_eac) < 1.0, (
            f"Expected EAC={expected_eac:.1f}, got {fc['eac']}"
        )

    def test_forecast_cpi_partial(self, client, db_session):
        self._seed(db_session)
        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()
        assert abs(fc["cpi"] - self._CPI) < 0.01, (
            f"Expected CPI={self._CPI:.3f}, got {fc['cpi']}"
        )


class TestSvIntegrity:
    """
    SV = actual_hours − planned_hours (positive = ahead, negative = behind schedule).

    Scenario:
      budget_hours=100, budget_cost=10_000
      Cycle 1 planned=40h, Cycle 2 planned=40h (cumulative baseline=80h by end C2)
      consumed (C1+C2)=60h, cost_per_hour=100 → AC=6_000
      EV  = (60/100)×10_000 = 6_000
      PV  = (80/100)×10_000 = 8_000
      SV  = 60h − 80h = −20h  (behind schedule)
      SPI = actual_hours / planned_hours = 60/80 = 0.750
    """

    PEP  = "60IT-777-01"
    DESC = "SV-Test"
    BH   = 100.0
    BC   = 10_000.0
    CPH  = 100.0

    _consumed = 60.0
    _cum_plan  = 80.0
    _EV  = (_consumed / BH) * BC    # 6_000
    _AC  = _consumed * CPH           # 6_000
    _PV  = (_cum_plan  / BH) * BC   # 8_000
    _SV  = _consumed - _cum_plan     # −20h (behind schedule)
    _SPI = _consumed / _cum_plan     # 0.750

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy1 = _cycle(db, "Jan/2026", 2026, 1)
        cy2 = _cycle(db, "Feb/2026", 2026, 2)
        co  = _collab(db, "Carol")
        p   = _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy1, co, self.PEP, self.DESC, normal=30.0, cph=self.CPH)
        _rec(db, cy2, co, self.PEP, self.DESC, normal=30.0, cph=self.CPH)
        _plan(db, p.id, cy1.id, planned_hours=40.0)
        _plan(db, p.id, cy2.id, planned_hours=40.0)
        return p

    def test_forecast_sv_sign(self, client, db_session):
        """SV must be negative when behind schedule."""
        self._seed(db_session)
        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()
        assert fc["sv"] is not None, "SV should not be None when PV is defined"
        assert fc["sv"] < 0, (
            f"Expected negative SV (behind schedule), got {fc['sv']}"
        )
        assert abs(fc["sv"] - self._SV) < 1.0, (
            f"Expected SV={self._SV:.1f}, got {fc['sv']}"
        )

    def test_forecast_spi(self, client, db_session):
        self._seed(db_session)
        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()
        assert fc["spi"] is not None
        assert abs(fc["spi"] - self._SPI) < 0.01, (
            f"Expected SPI={self._SPI:.3f}, got {fc['spi']}"
        )

    def test_runway_spi(self, client, db_session):
        """Runway SPI must match forecast SPI for the same scenario."""
        self._seed(db_session)

        runway = client.get("/api/v2/runway").json()
        ritem  = next((i for i in runway if i["pep_wbs"] == self.PEP), None)
        assert ritem is not None

        fc = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()

        assert ritem["spi"] is not None
        assert abs(ritem["spi"] - fc["spi"]) < 0.001, (
            f"SPI mismatch: runway={ritem['spi']}, forecast={fc['spi']}"
        )


class TestTrendsCpiConsistency:
    """
    Trends actual_cost must match runway and forecast AC.
    Runway and forecast CPI must be consistent with each other.
    """

    PEP  = "60IT-666-01"
    DESC = "Trends-CPI"
    BH   = 80.0
    BC   = 8_000.0
    NORM = 40.0
    CPH  = 50.0

    _EV  = (NORM / BH) * BC    # 4_000
    _AC  = NORM * CPH            # 2_000
    _CPI = _EV / _AC             # 2.000

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy = _cycle(db, "Mar/2026", 2026, 3)
        co = _collab(db, "Dan")
        p  = _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy, co, self.PEP, self.DESC, normal=self.NORM, cph=self.CPH)
        return p, cy

    def test_trends_actual_cost(self, client, db_session):
        self._seed(db_session)
        resp = client.get("/api/v2/trends")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        total_ac = sum(r["actual_cost"] for r in rows)
        assert abs(total_ac - self._AC) < 0.01, (
            f"Trends actual_cost={total_ac:.2f}, expected {self._AC:.2f}"
        )

    def test_trends_runway_consistency(self, client, db_session):
        self._seed(db_session)

        runway = client.get("/api/v2/runway").json()
        fc     = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}").json()

        ritem = next((i for i in runway if i["pep_wbs"] == self.PEP), None)
        r_cpi = ritem["cpi"] if ritem else None
        f_cpi = fc["cpi"]

        assert r_cpi is not None
        assert f_cpi is not None
        assert abs(r_cpi - f_cpi) < 0.01, f"Runway CPI={r_cpi} vs Forecast CPI={f_cpi}"


class TestEvmOverBudget:
    """
    Scenario: consumed_hours exceeds budget_hours (project over budget in effort).

    Without capping EV at BAC, the formula EV = (consumed/budget) × budget_cost
    yields EV > BAC, which makes CPI > 1 even though the project is massively
    over budget — a false positive that masks the overrun.

    With the cap: EV = min(consumed/budget, 1.0) × budget_cost

      budget_hours = 100
      budget_cost  = 10_000   (BAC)
      consumed     = 136 h    (136% of budget)
      cost_per_hour = 100 → AC = 13_600

      EV (capped)  = min(136/100, 1.0) × 10_000 = 10_000  (= BAC)
      CPI          = 10_000 / 13_600              = 0.735
      EAC          = 10_000 / 0.735               ≈ 13_600
    """

    PEP  = "60IT-OVR-01"
    DESC = "OverBudget"
    BH   = 100.0
    BC   = 10_000.0
    NORM = 136.0
    CPH  = 100.0

    _EV  = min(NORM / BH, 1.0) * BC   # 10_000 (capped at BAC)
    _AC  = NORM * CPH                  # 13_600
    _CPI = _EV / _AC                   # 0.7353

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy = _cycle(db, "Apr/2026", 2026, 4)
        co = _collab(db, "Oscar")
        p  = _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy, co, self.PEP, self.DESC, normal=self.NORM, cph=self.CPH)
        return p, cy

    def test_runway_cpi_over_budget(self, client, db_session):
        """CPI must be < 1 when consumed > budget, not inflated above 1."""
        self._seed(db_session)
        resp = client.get("/api/v2/runway")
        assert resp.status_code == 200
        item = next((i for i in resp.json() if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["cpi"] is not None
        assert item["cpi"] < 1.0, (
            f"CPI={item['cpi']:.4f} should be < 1.0 for an over-budget project; "
            f"EV cap at BAC is required."
        )
        assert abs(item["cpi"] - self._CPI) < 0.01, (
            f"Expected CPI={self._CPI:.4f}, got {item['cpi']:.4f}"
        )

    def test_forecast_cpi_over_budget(self, client, db_session):
        """Forecast CPI must also reflect cost overrun."""
        self._seed(db_session)
        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["cpi"] is not None
        assert fc["cpi"] < 1.0, f"Forecast CPI={fc['cpi']} should be < 1 for overrun project"
        assert abs(fc["cpi"] - self._CPI) < 0.01

    def test_trends_actual_cost_over_budget(self, client, db_session):
        """Trends actual_cost must reflect true AC for an over-budget project."""
        self._seed(db_session)
        resp = client.get("/api/v2/trends")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        total_ac = sum(r["actual_cost"] for r in rows)
        assert abs(total_ac - self._AC) < 0.01, (
            f"Trends actual_cost={total_ac:.2f}, expected {self._AC:.2f}"
        )


class TestMultiplierFallback:
    """
    When GlobalConfig is absent, em fallback=1.5, sm fallback=0.33 must match
    the seeded defaults in database.py so actual_cost is consistent with or
    without a config row.

    Scenario (standby only, to isolate sm):
      standby_hours = 10, cost_per_hour = 100, sm_fallback = 0.33
      actual_cost = 10 × 100 × 0.33 = 330
    """

    PEP  = "60IT-FAL-01"
    DESC = "Fallback"
    STANDBY = 10.0
    CPH = 100.0
    SM_FALLBACK = 0.33
    _AC_EXPECTED = STANDBY * CPH * SM_FALLBACK  # 330.0

    def _seed(self, db):
        # No GlobalConfig — forces the fallback branch
        cy = _cycle(db, "May/2026", 2026, 5)
        co = _collab(db, "Eve")
        _rec(db, cy, co, self.PEP, self.DESC, normal=0.0, standby=self.STANDBY, cph=self.CPH, sm=self.SM_FALLBACK)

    def test_trends_actual_cost_uses_sm_fallback(self, client, db_session):
        """actual_cost in /api/v2/trends must use sm=0.33 when GlobalConfig is absent."""
        self._seed(db_session)
        resp = client.get("/api/v2/trends")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 1
        ac = rows[0]["actual_cost"]
        assert abs(ac - self._AC_EXPECTED) < 0.01, (
            f"actual_cost={ac:.2f}, expected {self._AC_EXPECTED:.2f} "
            f"(standby×cph×sm=10×100×0.33). "
            f"Fallback sm must equal the seeded default of 0.33, not 1.0."
        )


class TestRunwayNegativeCyclesToComplete:
    """
    When consumed_hours > budget_hours the project is already overrun.
    cycles_to_complete must be null (not a negative number) in the API response.
    """

    PEP  = "60IT-NEG-01"
    DESC = "NegCycles"
    BH   = 50.0
    BC   = 5_000.0
    NORM = 80.0  # 60% over budget
    CPH  = 50.0

    def _seed(self, db):
        _global_config(db, em=1.0, sm=1.0)
        cy = _cycle(db, "Jun/2026", 2026, 6)
        co = _collab(db, "Frank")
        _project(db, self.PEP, self.BH, self.BC)
        _rec(db, cy, co, self.PEP, self.DESC, normal=self.NORM, cph=self.CPH)

    def test_cycles_to_complete_null_when_overrun(self, client, db_session):
        """cycles_to_complete must be null (not negative) for an over-budget project."""
        self._seed(db_session)
        resp = client.get("/api/v2/runway")
        assert resp.status_code == 200
        item = next((i for i in resp.json() if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["risk"] == "overrun"
        assert item["cycles_to_complete"] is None, (
            f"cycles_to_complete={item['cycles_to_complete']} should be null for overrun project"
        )


class TestRunwaySpiScenarios:
    """SPI scenarios for /api/v2/runway, focusing on freeze_spi_boundary correctness."""

    PEP  = "60IT-SPX-01"
    DESC = "SPI Test"

    def test_no_budget_risk_is_no_budget(self, client, db_session):
        """PEP with no budget → risk='no_budget', cpi=None, spi=None."""
        _global_config(db_session)
        cy = _cycle(db_session, "Jan/2026", 2026, 1)
        co = _collab(db_session, "Ana")
        p = Project(pep_wbs=self.PEP, name="NoBudget")
        db_session.add(p)
        db_session.flush()
        _rec(db_session, cy, co, self.PEP, self.DESC, normal=10.0, cph=50.0)

        resp = client.get("/api/v2/runway")
        item = next((i for i in resp.json() if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["risk"] == "no_budget"
        assert item["cpi"] is None
        assert item["spi"] is None

    def test_spi_present_when_plan_exists(self, client, db_session):
        """SPI must be non-None when a ProjectCyclePlan row exists for the project."""
        _global_config(db_session)
        cy = _cycle(db_session, "Feb/2026", 2026, 2)
        co = _collab(db_session, "Bob")
        p = _project(db_session, self.PEP, budget_hours=100.0, budget_cost=10_000.0)
        _rec(db_session, cy, co, self.PEP, self.DESC, normal=60.0, cph=100.0)
        _plan(db_session, p.id, cy.id, planned_hours=80.0)

        resp = client.get("/api/v2/runway")
        item = next((i for i in resp.json() if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["spi"] is not None, "SPI should be present when a ProjectCyclePlan exists"
        assert item["schedule_status"] != "no_baseline"

    def test_spi_overrun_hours_uses_actual_ratio(self, client, db_session):
        """SPI uses raw hours ratio when consumed > budget_hours.

        Old bug: compute_ev_capped capped EV at BAC, so the ratio diverged from
        actual_h/planned_h when running_h > budget_hours.
        freeze_spi_boundary works in hours throughout, so the ratio is correct.

        Setup: budget=100h, planned=50h, consumed=120h
          hours-based SPI = 120 / 50 = 2.40
          old R$-capped   = min(120/100,1.0)×10000 / (50/100×10000) = 10000/5000 = 2.00
        """
        _global_config(db_session)
        cy = _cycle(db_session, "Mar/2026", 2026, 3)
        co = _collab(db_session, "Carol")
        p = _project(db_session, self.PEP, budget_hours=100.0, budget_cost=10_000.0)
        _rec(db_session, cy, co, self.PEP, self.DESC, normal=120.0, cph=100.0)
        _plan(db_session, p.id, cy.id, planned_hours=50.0)

        resp = client.get("/api/v2/runway")
        item = next((i for i in resp.json() if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["spi"] == pytest.approx(2.4, abs=0.01), (
            f"Expected hours-based SPI=2.4, got {item['spi']} "
            "(old R$-capped code would give 2.0)"
        )


# ---------------------------------------------------------------------------
# GR-2-02 Regression: cpi_cumulative in forecast history
# ---------------------------------------------------------------------------

class TestCpiCumulativeInHistory:
    """GR-2-02: forecast history entries must include cpi_cumulative computed
    server-side so the frontend does not divide ev / cost client-side."""

    PEP  = "INT-CPI-CUM"
    DESC = "CPI-Cum Test"

    def test_history_has_cpi_cumulative(self, client, db_session):
        _global_config(db_session)
        cy = _cycle(db_session, "Jan/2026-CUM", 2026, 1)
        co = _collab(db_session, "CumUser")
        _project(db_session, self.PEP, budget_hours=100.0, budget_cost=10_000.0)
        _rec(db_session, cy, co, self.PEP, self.DESC, normal=50.0, cph=100.0)

        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["history"], "Expected at least one history entry"
        for entry in fc["history"]:
            assert "cpi_cumulative" in entry, (
                f"GR-2-02: cpi_cumulative missing from history entry {entry['cycle_name']}"
            )

    def test_cpi_cumulative_matches_ev_over_ac(self, client, db_session):
        """cpi_cumulative must equal compute_cpi(ev_cost, ac) = ev/ac."""
        _global_config(db_session)
        cy = _cycle(db_session, "Jan/2026-EV", 2026, 1)
        co = _collab(db_session, "EVUser")
        _project(db_session, self.PEP + "2", budget_hours=100.0, budget_cost=10_000.0)
        # consumed=50h → EV = 50/100 * 10000 = 5000; AC = 50*100 = 5000; CPI = 1.0
        _rec(db_session, cy, co, self.PEP + "2", self.DESC, normal=50.0, cph=100.0)

        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}2")
        assert resp.status_code == 200
        fc = resp.json()
        entry = fc["history"][-1]
        assert entry["cpi_cumulative"] == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# AR-01 Regression: spi_t_color must be present in forecast response
# ---------------------------------------------------------------------------

class TestSpiTColorInForecast:
    """AR-01: forecast response must include spi_t_color (server-computed)
    so the frontend does not hardcode the 0.8 threshold."""

    PEP  = "INT-SPIT-COL"
    DESC = "SPI-t Color Test"

    def test_spi_t_color_present_in_response(self, client, db_session):
        _global_config(db_session)
        cy = _cycle(db_session, "Jan/2026-SPIT", 2026, 1)
        co = _collab(db_session, "SpitUser")
        p = _project(db_session, self.PEP, budget_hours=100.0, budget_cost=10_000.0)
        _rec(db_session, cy, co, self.PEP, self.DESC, normal=50.0, cph=100.0)
        _plan(db_session, p.id, cy.id, planned_hours=50.0)

        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert "spi_t_color" in fc, "AR-01: spi_t_color must be present in forecast response"

    def test_spi_t_color_valid_values(self, client, db_session):
        """spi_t_color must be None or one of success/warning/danger."""
        _global_config(db_session)
        cy = _cycle(db_session, "Feb/2026-SPIT", 2026, 2)
        co = _collab(db_session, "SpitUser2")
        p = _project(db_session, self.PEP + "2", budget_hours=100.0, budget_cost=10_000.0)
        _rec(db_session, cy, co, self.PEP + "2", self.DESC, normal=50.0, cph=100.0)
        _plan(db_session, p.id, cy.id, planned_hours=50.0)

        resp = client.get(f"/api/v2/forecast?pep_wbs={self.PEP}2")
        assert resp.status_code == 200
        color = resp.json().get("spi_t_color")
        assert color in (None, "success", "warning", "danger"), (
            f"spi_t_color must be None or a valid status string, got {color!r}"
        )
