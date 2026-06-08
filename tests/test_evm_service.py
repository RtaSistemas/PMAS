"""Unit tests for EVM service functions — pure math, no DB.

Every function in evm.py is exercised here: happy path, boundary conditions,
and None-guard cases.  These tests run without a database or HTTP client.
"""
from __future__ import annotations

import pytest

from backend.app.services.evm import (
    compute_earned_schedule, compute_spi_t, compute_sv_t, compute_ieac_t,
)


class TestEarnedSchedule:
    def test_midpoint(self):
        assert compute_earned_schedule(150.0, [100.0, 200.0, 300.0]) == pytest.approx(1.5)

    def test_exact_boundary(self):
        assert compute_earned_schedule(200.0, [100.0, 200.0, 300.0]) == pytest.approx(2.0)

    def test_capped_at_max(self):
        assert compute_earned_schedule(350.0, [100.0, 200.0, 300.0]) == pytest.approx(3.0)

    def test_zero_ev_returns_none(self):
        assert compute_earned_schedule(0.0, [100.0, 200.0]) is None

    def test_none_ev_returns_none(self):
        assert compute_earned_schedule(None, [100.0, 200.0]) is None

    def test_empty_curve_returns_none(self):
        assert compute_earned_schedule(50.0, []) is None

    def test_first_period(self):
        # EV = 50, PV at t=1 is 100 → ES = 0.5
        assert compute_earned_schedule(50.0, [100.0, 200.0]) == pytest.approx(0.5)


class TestSpiT:
    def test_normal(self):
        assert compute_spi_t(1.5, 2.0) == pytest.approx(0.75)

    def test_on_schedule(self):
        assert compute_spi_t(3.0, 3.0) == pytest.approx(1.0)

    def test_zero_at_returns_none(self):
        assert compute_spi_t(1.5, 0.0) is None

    def test_none_es_returns_none(self):
        assert compute_spi_t(None, 2.0) is None


class TestSvT:
    def test_behind(self):
        assert compute_sv_t(1.5, 2.0) == pytest.approx(-0.5)

    def test_ahead(self):
        assert compute_sv_t(2.5, 2.0) == pytest.approx(0.5)

    def test_none_es_returns_none(self):
        assert compute_sv_t(None, 2.0) is None


class TestIeacT:
    def test_normal(self):
        assert compute_ieac_t(4.0, 0.75) == pytest.approx(5.33, rel=0.01)

    def test_zero_spi_returns_none(self):
        assert compute_ieac_t(4.0, 0.0) is None

    def test_none_spi_returns_none(self):
        assert compute_ieac_t(4.0, None) is None

    def test_none_pd_returns_none(self):
        assert compute_ieac_t(None, 0.8) is None


from backend.app.services.evm import (
    classify_health,
    compute_cpi,
    compute_cv,
    compute_eac,
    compute_eac_schedule,
    compute_ev_cost,
    compute_period_delta,
    compute_period_delta_pct,
    compute_spi,
    compute_sv,
    compute_tcpi,
    compute_vac,
    cv_label,
    freeze_costs,
    tcpi_label,
    vac_color,
    vac_label,
)


# ── freeze_costs ──────────────────────────────────────────────────────────────

class TestFreezeCosts:
    def test_normal_only(self):
        nc, ec, sc = freeze_costs(8.0, 0.0, 0.0, cost_per_hour=50.0, extra_multiplier=1.5, standby_multiplier=1.25)
        assert nc == 400.0
        assert ec == 0.0
        assert sc == 0.0

    def test_extra_multiplied(self):
        nc, ec, sc = freeze_costs(0.0, 2.0, 0.0, cost_per_hour=50.0, extra_multiplier=1.5, standby_multiplier=1.0)
        assert ec == pytest.approx(150.0)

    def test_standby_multiplied(self):
        nc, ec, sc = freeze_costs(0.0, 0.0, 1.0, cost_per_hour=50.0, extra_multiplier=1.0, standby_multiplier=1.25)
        assert sc == pytest.approx(62.5)

    def test_all_types(self):
        nc, ec, sc = freeze_costs(8.0, 2.0, 1.0, cost_per_hour=50.0, extra_multiplier=1.5, standby_multiplier=1.25)
        assert nc == pytest.approx(400.0)
        assert ec == pytest.approx(150.0)
        assert sc == pytest.approx(62.5)

    def test_zero_rate(self):
        nc, ec, sc = freeze_costs(8.0, 2.0, 1.0, cost_per_hour=0.0, extra_multiplier=1.5, standby_multiplier=1.25)
        assert nc == ec == sc == 0.0

    def test_result_is_frozen_tuple(self):
        result = freeze_costs(4.0, 1.0, 0.0, 100.0, 1.5, 1.0)
        assert isinstance(result, tuple)
        assert len(result) == 3


# ── compute_cpi ───────────────────────────────────────────────────────────────
# compute_cpi(ev_cost, actual_cost): first arg is true Earned Value, NOT BAC.
# Use compute_ev_capped() to obtain the correct ev_cost.

class TestComputeCpi:
    def test_on_budget(self):
        # EV == AC → CPI = 1.0
        assert compute_cpi(10_000.0, 10_000.0) == pytest.approx(1.0)

    def test_under_budget(self):
        # EV=10k, AC=8k → earned more than spent → CPI > 1
        assert compute_cpi(10_000.0, 8_000.0) == pytest.approx(1.25)

    def test_over_budget(self):
        # EV=10k, AC=12k → spent more than earned → CPI < 1
        assert compute_cpi(10_000.0, 12_000.0) == pytest.approx(0.8333, abs=1e-3)

    def test_in_progress_project_uses_ev_not_bac(self):
        # Project: BAC=10_000, consumed=50% of hours, AC=5_500
        # EV = min(0.5, 1.0) × 10_000 = 5_000
        # CPI = EV/AC = 5_000/5_500 ≈ 0.909  (over budget)
        # (passing BAC=10_000 instead of EV=5_000 would give 10_000/5_500≈1.818 — wrong)
        ev = 5_000.0   # from compute_ev_capped(consumed_h=50, budget_h=100, budget_c=10_000)
        assert compute_cpi(ev, 5_500.0) == pytest.approx(0.9091, abs=1e-3)

    def test_zero_actual_returns_none(self):
        assert compute_cpi(10_000.0, 0.0) is None

    def test_none_ev_returns_none(self):
        assert compute_cpi(None, 5_000.0) is None

    def test_zero_ev_returns_none(self):
        assert compute_cpi(0.0, 5_000.0) is None


# ── compute_spi ───────────────────────────────────────────────────────────────

class TestComputeSpi:
    def test_on_schedule(self):
        assert compute_spi(100.0, 100.0) == pytest.approx(1.0)

    def test_ahead(self):
        assert compute_spi(80.0, 100.0) == pytest.approx(1.25)

    def test_behind(self):
        assert compute_spi(100.0, 75.0) == pytest.approx(0.75)

    def test_zero_planned_returns_none(self):
        assert compute_spi(0.0, 50.0) is None

    def test_none_planned_returns_none(self):
        assert compute_spi(None, 50.0) is None


# ── compute_eac ───────────────────────────────────────────────────────────────

class TestComputeEac:
    def test_normal(self):
        # CPI=0.5 → EAC = BAC / 0.5 = 20_000
        assert compute_eac(10_000.0, 0.5) == pytest.approx(20_000.0)

    def test_cpi_1_returns_bac(self):
        assert compute_eac(10_000.0, 1.0) == pytest.approx(10_000.0)

    def test_none_budget_returns_none(self):
        assert compute_eac(None, 0.8) is None

    def test_none_cpi_returns_none(self):
        assert compute_eac(10_000.0, None) is None

    def test_none_cpi_default_to_bac(self):
        # When no performance data yet, EAC should default to BAC
        assert compute_eac(10_000.0, None, default_to_bac=True) == pytest.approx(10_000.0)

    def test_zero_cpi_returns_none(self):
        assert compute_eac(10_000.0, 0.0) is None


# ── compute_eac_schedule ─────────────────────────────────────────────────────

class TestComputeEacSchedule:
    def test_behind_schedule_raises_eac(self):
        # BAC=10_000, AC=4_000, EV=4_000, CPI=1.0, SPI=0.8
        # EAC = 4_000 + (10_000 − 4_000) / (1.0 × 0.8) = 4_000 + 7_500 = 11_500
        result = compute_eac_schedule(10_000.0, 4_000.0, 4_000.0, 1.0, 0.8)
        assert result == pytest.approx(11_500.0)

    def test_on_schedule_equals_cpi_eac(self):
        # SPI=1.0 → EAC_schedule == EAC_cpi = BAC/CPI
        # BAC=10_000, AC=4_400, EV=4_000, CPI≈0.909, SPI=1.0
        # EAC = 4_400 + (10_000 − 4_000) / (0.909×1.0) ≈ 10_999.9... ≈ 11_000
        result = compute_eac_schedule(10_000.0, 4_400.0, 4_000.0, 4_000/4_400, 1.0)
        assert result == pytest.approx(10_000.0 / (4_000/4_400), abs=1.0)

    def test_none_budget_returns_none(self):
        assert compute_eac_schedule(None, 4_000.0, 4_000.0, 1.0, 1.0) is None

    def test_none_ev_returns_none(self):
        assert compute_eac_schedule(10_000.0, 4_000.0, None, 1.0, 1.0) is None

    def test_none_cpi_returns_none(self):
        assert compute_eac_schedule(10_000.0, 4_000.0, 4_000.0, None, 1.0) is None

    def test_none_spi_returns_none(self):
        assert compute_eac_schedule(10_000.0, 4_000.0, 4_000.0, 1.0, None) is None

    def test_zero_spi_returns_none(self):
        assert compute_eac_schedule(10_000.0, 4_000.0, 4_000.0, 1.0, 0.0) is None


# ── compute_tcpi ──────────────────────────────────────────────────────────────

class TestComputeTcpi:
    def test_normal(self):
        # BAC=10_000, AC=4_000, EV=5_000
        # TCPI = (BAC-EV)/(BAC-AC) = 5_000/6_000 = 0.8333
        result = compute_tcpi(10_000.0, 4_000.0, ev_cost=5_000.0)
        assert result == pytest.approx(0.8333, abs=1e-3)

    def test_no_budget_returns_none(self):
        assert compute_tcpi(None, 4_000.0, ev_cost=5_000.0) is None

    def test_no_ev_returns_none(self):
        assert compute_tcpi(10_000.0, 4_000.0, ev_cost=None) is None

    def test_bac_equals_ac_returns_none(self):
        # denominator = BAC - AC = 0
        assert compute_tcpi(10_000.0, 10_000.0, ev_cost=8_000.0) is None


# ── compute_vac ───────────────────────────────────────────────────────────────

class TestComputeVac:
    def test_under_budget(self):
        # BAC=10_000, EAC=8_000 → VAC=2_000 (positive = savings)
        assert compute_vac(10_000.0, 8_000.0) == pytest.approx(2_000.0)

    def test_over_budget(self):
        assert compute_vac(10_000.0, 12_000.0) == pytest.approx(-2_000.0)

    def test_none_budget_returns_none(self):
        assert compute_vac(None, 8_000.0) is None

    def test_none_eac_returns_none(self):
        assert compute_vac(10_000.0, None) is None


# ── compute_cv ────────────────────────────────────────────────────────────────

class TestComputeCv:
    def test_under_budget(self):
        # EV=6_000, AC=5_000 → CV = +1_000 (positive = under budget)
        assert compute_cv(6_000.0, 5_000.0) == pytest.approx(1_000.0)

    def test_over_budget(self):
        assert compute_cv(5_000.0, 6_000.0) == pytest.approx(-1_000.0)

    def test_none_ev_returns_none(self):
        assert compute_cv(None, 5_000.0) is None

    def test_zero_cv(self):
        assert compute_cv(5_000.0, 5_000.0) == pytest.approx(0.0)


# ── compute_ev_cost ───────────────────────────────────────────────────────────

class TestComputeEvCost:
    def test_normal(self):
        # blended_rate = 10_000 / 200 = 50; EV = 100 × 50 = 5_000
        assert compute_ev_cost(100.0, 10_000.0, 200.0) == pytest.approx(5_000.0)

    def test_none_budget_cost_returns_none(self):
        assert compute_ev_cost(100.0, None, 200.0) is None

    def test_none_budget_hours_returns_none(self):
        assert compute_ev_cost(100.0, 10_000.0, None) is None

    def test_zero_budget_hours_returns_none(self):
        assert compute_ev_cost(100.0, 10_000.0, 0.0) is None

    def test_full_completion(self):
        # 200/200 h consumed → EV = BAC
        assert compute_ev_cost(200.0, 10_000.0, 200.0) == pytest.approx(10_000.0)


# ── compute_sv ────────────────────────────────────────────────────────────────

class TestComputeSv:
    def test_behind(self):
        # actual=60, planned=80 → SV = -20 (behind)
        assert compute_sv(60.0, 80.0) == pytest.approx(-20.0)

    def test_ahead(self):
        assert compute_sv(90.0, 80.0) == pytest.approx(10.0)

    def test_on_schedule(self):
        assert compute_sv(80.0, 80.0) == pytest.approx(0.0)

    def test_none_planned_returns_none(self):
        assert compute_sv(60.0, None) is None


# ── compute_period_delta ──────────────────────────────────────────────────────

class TestComputePeriodDelta:
    def test_increase(self):
        assert compute_period_delta(50.0, 40.0) == pytest.approx(10.0)

    def test_decrease(self):
        assert compute_period_delta(30.0, 40.0) == pytest.approx(-10.0)

    def test_first_period_returns_none(self):
        assert compute_period_delta(50.0, None) is None

    def test_zero_delta(self):
        assert compute_period_delta(40.0, 40.0) == pytest.approx(0.0)


# ── compute_period_delta_pct ──────────────────────────────────────────────────

class TestComputePeriodDeltaPct:
    def test_increase_50pct(self):
        assert compute_period_delta_pct(60.0, 40.0) == pytest.approx(50.0)

    def test_decrease_25pct(self):
        assert compute_period_delta_pct(30.0, 40.0) == pytest.approx(-25.0)

    def test_first_period_returns_none(self):
        assert compute_period_delta_pct(50.0, None) is None

    def test_zero_previous_returns_none(self):
        assert compute_period_delta_pct(50.0, 0.0) is None


# ── classify_health ───────────────────────────────────────────────────────────

class TestClassifyHealth:
    def test_ok(self):
        assert classify_health(80.0, 100.0) == "ok"

    def test_warning_at_threshold(self):
        # exactly at 90% → warning
        assert classify_health(90.0, 100.0) == "warning"

    def test_warning_just_below_critical(self):
        assert classify_health(99.9, 100.0) == "warning"

    def test_overrun_at_100pct(self):
        # exactly at critical_threshold (1.0) → overrun (no dead "critical" state)
        assert classify_health(100.0, 100.0) == "overrun"

    def test_overrun_above_critical(self):
        assert classify_health(101.0, 100.0) == "overrun"

    def test_no_budget_none(self):
        assert classify_health(50.0, None) == "no_budget"

    def test_no_budget_zero(self):
        assert classify_health(50.0, 0.0) == "no_budget"

    def test_custom_thresholds(self):
        # With thresholds 80%/90%:
        # 85% → warning (≥0.8, <0.9)
        # 90% → overrun (≥ critical_threshold)
        # 95% → overrun (> critical_threshold)
        assert classify_health(85.0, 100.0, warning_threshold=0.8, critical_threshold=0.9) == "warning"
        assert classify_health(90.0, 100.0, warning_threshold=0.8, critical_threshold=0.9) == "overrun"
        assert classify_health(95.0, 100.0, warning_threshold=0.8, critical_threshold=0.9) == "overrun"


# ── tcpi_label ────────────────────────────────────────────────────────────────

class TestTcpiLabel:
    def test_achievable(self):
        assert "alcançável" in tcpi_label(0.95)

    def test_exactly_1(self):
        assert "alcançável" in tcpi_label(1.0)

    def test_tight(self):
        assert "apertada" in tcpi_label(1.05)
        assert "5%" in tcpi_label(1.05)

    def test_exactly_1_1(self):
        assert "apertada" in tcpi_label(1.1)
        assert "10%" in tcpi_label(1.1)

    def test_unachievable(self):
        assert "inviável" in tcpi_label(1.25)
        assert "25%" in tcpi_label(1.25)

    def test_none_returns_none(self):
        assert tcpi_label(None) is None


# ── cv_label(0) fix ───────────────────────────────────────────────────────────

class TestCvLabelFix:
    def test_zero_cv_is_no_orcamento(self):
        assert cv_label(0) == "No orçamento"

    def test_zero_cv_not_no_prazo(self):
        assert cv_label(0) != "No prazo"

    def test_positive_cv(self):
        assert "Economia" in cv_label(1000.0)

    def test_negative_cv(self):
        assert "Estouro" in cv_label(-500.0)


# ── vac_label / vac_color ─────────────────────────────────────────────────────

class TestVacLabelColor:
    def test_positive_vac_label(self):
        assert "Economia" in vac_label(5000.0)

    def test_negative_vac_label(self):
        assert "Estouro" in vac_label(-3000.0)

    def test_zero_vac_label(self):
        assert vac_label(0) == "No orçamento"

    def test_none_label(self):
        assert vac_label(None) is None

    def test_positive_vac_color_success(self):
        assert vac_color(5000.0) == "success"

    def test_negative_vac_color_danger(self):
        assert vac_color(-3000.0) == "danger"

    def test_zero_vac_color_success(self):
        assert vac_color(0) == "success"

    def test_none_color(self):
        assert vac_color(None) is None
