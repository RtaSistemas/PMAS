"""EVM calculation integrity tests.

Verifies that CPI, EAC, and SV are computed with the correct formulas and
produce consistent results across /api/portfolio-health (runway),
/api/trends, and /api/projects/{id}/forecast.

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


def _rec(db, cycle, collab, pep, desc, normal, extra=0.0, standby=0.0, day=10, cph=100.0):
    r = TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id,
        record_date=date(cycle.start_date.year, cycle.start_date.month, day),
        pep_wbs=pep, pep_description=desc,
        normal_hours=float(normal), extra_hours=float(extra), standby_hours=float(standby),
        cost_per_hour=float(cph),
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
        resp = client.get("/api/portfolio-health")
        assert resp.status_code == 200
        items = resp.json()
        item = next((i for i in items if i["pep_wbs"] == self.PEP), None)
        assert item is not None, "PEP not found in portfolio-health"
        assert abs(item["consumed_hours"] - self.NORMAL) < 0.01
        assert abs(item["actual_cost"]    - self._AC)    < 0.01

    def test_runway_cpi(self, client, db_session):
        """CPI from /api/portfolio-runway must use EV/AC, not BAC/AC."""
        self._seed(db_session)
        resp = client.get("/api/portfolio-runway")
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
        """CPI from /api/forecast must match runway CPI."""
        self._seed(db_session)
        resp = client.get(f"/api/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["cpi"] is not None, "Forecast CPI should not be None"
        assert abs(fc["cpi"] - self._CPI) < 0.01, (
            f"Forecast CPI={fc['cpi']:.4f}, expected {self._CPI:.4f}."
        )

    def test_cpi_consistency_runway_vs_forecast(self, client, db_session):
        """Runway and forecast must return the same CPI value."""
        self._seed(db_session)

        runway = client.get("/api/portfolio-runway").json()
        ritem  = next((i for i in runway if i["pep_wbs"] == self.PEP), None)

        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()

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
        resp  = client.get("/api/portfolio-runway").json()
        item  = next((i for i in resp if i["pep_wbs"] == self.PEP), None)
        assert item is not None
        assert item["cpi"] is not None
        assert abs(item["cpi"] - self._CPI) < 0.01, (
            f"Expected CPI={self._CPI:.3f}, got {item['cpi']}"
        )

    def test_forecast_eac(self, client, db_session):
        """EAC = budget_cost / CPI — should flag overrun when CPI<1."""
        self._seed(db_session)
        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()
        expected_eac = self.BC / self._CPI   # 20_000
        assert fc["eac"] is not None
        assert abs(fc["eac"] - expected_eac) < 1.0, (
            f"Expected EAC={expected_eac:.1f}, got {fc['eac']}"
        )

    def test_forecast_cpi_partial(self, client, db_session):
        self._seed(db_session)
        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()
        assert abs(fc["cpi"] - self._CPI) < 0.01, (
            f"Expected CPI={self._CPI:.3f}, got {fc['cpi']}"
        )


class TestSvIntegrity:
    """
    SV = EV − PV (positive = ahead, negative = behind schedule).

    Scenario:
      budget_hours=100, budget_cost=10_000
      Cycle 1 planned=40h, Cycle 2 planned=40h (cumulative baseline=80h by end C2)
      consumed (C1+C2)=60h, cost_per_hour=100 → AC=6_000
      EV  = (60/100)×10_000 = 6_000
      PV  = (80/100)×10_000 = 8_000
      SV  = 6_000 − 8_000   = −2_000  (behind)
      SPI = EV/PV            = 6_000/8_000 = 0.750
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
    _SV  = _EV - _PV                 # −2_000 (behind)
    _SPI = _EV / _PV                 # 0.750

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
        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()
        assert fc["sv"] is not None, "SV should not be None when PV is defined"
        assert fc["sv"] < 0, (
            f"Expected negative SV (behind schedule), got {fc['sv']}"
        )
        assert abs(fc["sv"] - self._SV) < 1.0, (
            f"Expected SV={self._SV:.1f}, got {fc['sv']}"
        )

    def test_forecast_spi(self, client, db_session):
        self._seed(db_session)
        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()
        assert fc["spi"] is not None
        assert abs(fc["spi"] - self._SPI) < 0.01, (
            f"Expected SPI={self._SPI:.3f}, got {fc['spi']}"
        )

    def test_runway_spi(self, client, db_session):
        """Runway SPI must match forecast SPI for the same scenario."""
        self._seed(db_session)

        runway = client.get("/api/portfolio-runway").json()
        ritem  = next((i for i in runway if i["pep_wbs"] == self.PEP), None)
        assert ritem is not None

        fc = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()

        assert ritem["spi"] is not None
        assert abs(ritem["spi"] - fc["spi"]) < 0.001, (
            f"SPI mismatch: runway={ritem['spi']}, forecast={fc['spi']}"
        )


class TestTrendsCpiConsistency:
    """
    Trends endpoint aggregates CPI over cycles.
    With a single cycle, trends CPI must match runway + forecast CPI.
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

    def test_trends_cpi(self, client, db_session):
        self._seed(db_session)
        resp = client.get("/api/trends")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) >= 1
        row = rows[-1]
        assert row["cpi"] is not None
        assert abs(row["cpi"] - self._CPI) < 0.01, (
            f"Trends CPI={row['cpi']:.4f}, expected {self._CPI:.4f}"
        )

    def test_trends_runway_consistency(self, client, db_session):
        self._seed(db_session)

        trends = client.get("/api/trends").json()
        runway = client.get("/api/portfolio-runway").json()
        fc     = client.get(f"/api/forecast?pep_wbs={self.PEP}").json()

        ritem = next((i for i in runway if i["pep_wbs"] == self.PEP), None)
        t_cpi = trends[-1]["cpi"]
        r_cpi = ritem["cpi"] if ritem else None
        f_cpi = fc["cpi"]

        assert t_cpi is not None
        assert r_cpi is not None
        assert f_cpi is not None
        assert abs(t_cpi - r_cpi) < 0.01, f"Trends CPI={t_cpi} vs Runway CPI={r_cpi}"
        assert abs(t_cpi - f_cpi) < 0.01, f"Trends CPI={t_cpi} vs Forecast CPI={f_cpi}"


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
        resp = client.get("/api/portfolio-runway")
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
        resp = client.get(f"/api/forecast?pep_wbs={self.PEP}")
        assert resp.status_code == 200
        fc = resp.json()
        assert fc["cpi"] is not None
        assert fc["cpi"] < 1.0, f"Forecast CPI={fc['cpi']} should be < 1 for overrun project"
        assert abs(fc["cpi"] - self._CPI) < 0.01

    def test_trends_cpi_over_budget(self, client, db_session):
        """Trends CPI must also reflect cost overrun."""
        self._seed(db_session)
        resp = client.get("/api/trends")
        assert resp.status_code == 200
        rows = resp.json()
        row = next((r for r in rows if r.get("cpi") is not None), None)
        assert row is not None
        assert row["cpi"] < 1.0, f"Trends CPI={row['cpi']} should be < 1 for overrun project"
        assert abs(row["cpi"] - self._CPI) < 0.01
