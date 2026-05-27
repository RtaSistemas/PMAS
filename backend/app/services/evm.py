"""EVM calculation functions — single source of truth.

Every EVM metric (CPI, SPI, EAC, EV, …) must be computed through
a function defined here.  No other file may re-implement these formulas.
"""
from __future__ import annotations

from typing import Optional


# ── Cost freezing ────────────────────────────────────────────────────────────

def freeze_costs(
    normal_hours: float,
    extra_hours: float,
    standby_hours: float,
    cost_per_hour: float,
    extra_multiplier: float,
    standby_multiplier: float,
) -> tuple[float, float, float]:
    """Compute (normal_cost, extra_cost, standby_cost) at ingestion time.

    Frozen at the moment of upload so future GlobalConfig changes do not
    retroactively alter historical cost figures.
    """
    normal_cost  = round(normal_hours  * cost_per_hour,                         4)
    extra_cost   = round(extra_hours   * cost_per_hour * extra_multiplier,       4)
    standby_cost = round(standby_hours * cost_per_hour * standby_multiplier,     4)
    return normal_cost, extra_cost, standby_cost


# ── Core EVM metrics ─────────────────────────────────────────────────────────

def compute_cpi(
    budget_cost: Optional[float],
    actual_cost: float,
) -> Optional[float]:
    """Cost Performance Index = EV / AC.  Proxy: EV = budget_cost (BAC).

    Returns None when actual_cost == 0 or budget is undefined.
    > 1.0 → under budget;  < 1.0 → over budget.
    """
    if not budget_cost or actual_cost == 0:
        return None
    return round(budget_cost / actual_cost, 4)


def compute_cpi_ev(
    consumed_hours: float,
    budget_hours: Optional[float],
    budget_cost: Optional[float],
    actual_cost: float,
) -> Optional[float]:
    """CPI = EV / AC using proper earned-value: EV = min(consumed/budget, 1.0) × BAC.

    Caps EV at BAC so a project cannot earn more value than its budget.
    Returns None when any required input is missing or zero.
    > 1.0 → under budget;  < 1.0 → over budget.
    """
    if not budget_hours or budget_hours == 0:
        return None
    if not budget_cost:
        return None
    if actual_cost == 0:
        return None
    ev = min(consumed_hours / budget_hours, 1.0) * budget_cost
    return round(ev / actual_cost, 4)


def compute_spi(
    cumulative_planned_hours: Optional[float],
    cumulative_actual_hours: float,
) -> Optional[float]:
    """Schedule Performance Index = EV_hours / PV_hours.

    Returns None when planned hours are undefined or zero.
    > 1.0 → ahead of schedule;  < 1.0 → behind.
    """
    if not cumulative_planned_hours or cumulative_planned_hours == 0:
        return None
    return round(cumulative_actual_hours / cumulative_planned_hours, 4)


def compute_eac(
    budget_cost: Optional[float],
    cpi: Optional[float],
) -> Optional[float]:
    """Estimate at Completion = BAC / CPI."""
    if not budget_cost or not cpi or cpi == 0:
        return None
    return round(budget_cost / cpi, 2)


def compute_tcpi(
    budget_cost: Optional[float],
    actual_cost: float,
    ev_cost: Optional[float],
) -> Optional[float]:
    """To-Complete Performance Index = (BAC − EV) / (BAC − AC).

    Measures the efficiency needed to finish within the original budget.
    """
    if not budget_cost or ev_cost is None:
        return None
    denominator = budget_cost - actual_cost
    if denominator == 0:
        return None
    return round((budget_cost - ev_cost) / denominator, 4)


def compute_vac(
    budget_cost: Optional[float],
    eac: Optional[float],
) -> Optional[float]:
    """Variance at Completion = BAC − EAC.

    Positive → under budget; Negative → over budget.
    """
    if not budget_cost or not eac:
        return None
    return round(budget_cost - eac, 2)


def compute_cv(
    ev_cost: Optional[float],
    actual_cost: float,
) -> Optional[float]:
    """Cost Variance = EV − AC.

    Positive → under budget; Negative → over budget.
    """
    if ev_cost is None:
        return None
    return round(ev_cost - actual_cost, 2)


def compute_ev_cost(
    cumulative_hours: float,
    budget_cost: Optional[float],
    budget_hours: Optional[float],
) -> Optional[float]:
    """Earned Value in R$ using the blended planned rate.

    EV = cumulative_hours × (budget_cost / budget_hours)

    Used for the burn-up chart's EV series and for SPI cost-based calculation.
    Returns None when budget is undefined.
    """
    if not budget_cost or not budget_hours or budget_hours == 0:
        return None
    return round(cumulative_hours * (budget_cost / budget_hours), 2)


# ── Variance / delta ─────────────────────────────────────────────────────────

def compute_sv(
    cumulative_actual_hours: float,
    cumulative_planned_hours: Optional[float],
) -> Optional[float]:
    """Schedule Variance (hours) = EV_hours − PV_hours.

    Positive → ahead of schedule; Negative → behind.
    """
    if cumulative_planned_hours is None:
        return None
    return round(cumulative_actual_hours - cumulative_planned_hours, 2)


def compute_period_delta(
    current: float,
    previous: Optional[float],
) -> Optional[float]:
    """Absolute variation between the current and previous period.

    Used in the Trends chart to show cycle-over-cycle change.
    """
    if previous is None:
        return None
    return round(current - previous, 2)


def compute_period_delta_pct(
    current: float,
    previous: Optional[float],
) -> Optional[float]:
    """Percentage variation between the current and previous period.

    Returns None when previous == 0.
    """
    if previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


# ── Health classification ─────────────────────────────────────────────────────

def classify_health(
    consumed: float,
    budget: Optional[float],
    warning_threshold: float = 0.9,
    critical_threshold: float = 1.0,
) -> str:
    """Classify consumption against budget.

    Returns one of: 'ok' | 'warning' | 'critical' | 'overrun' | 'no_budget'.
    """
    if not budget or budget == 0:
        return "no_budget"
    ratio = consumed / budget
    if ratio > critical_threshold:
        return "overrun"
    if ratio >= critical_threshold:
        return "critical"
    if ratio >= warning_threshold:
        return "warning"
    return "ok"


# ── Capped Earned Value ───────────────────────────────────────────────────────

def compute_ev_capped(
    consumed_hours: float,
    budget_hours: Optional[float],
    budget_cost: Optional[float],
) -> Optional[float]:
    """Earned Value capped at BAC: EV = min(consumed / budget, 1.0) × BAC.

    Used for SPI, CPI, EAC, and other forecast indicators where EV must
    not exceed the Budget at Completion.  Distinct from compute_ev_cost
    (uncapped, used for the burn-up chart's EV series).
    """
    if not budget_hours or budget_hours == 0 or not budget_cost:
        return None
    return round(min(consumed_hours / budget_hours, 1.0) * budget_cost, 2)


# ── Color / label classifiers ─────────────────────────────────────────────────

def cpi_color(cpi: Optional[float]) -> Optional[str]:
    """Return 'success' / 'warning' / 'danger' for CPI, or None."""
    if cpi is None:
        return None
    if cpi >= 1.0:
        return "success"
    if cpi >= 0.9:
        return "warning"
    return "danger"


def cpi_label(cpi: Optional[float]) -> Optional[str]:
    """Return human-readable CPI label in pt-BR."""
    if cpi is None:
        return None
    return "Dentro do orçamento" if cpi >= 1.0 else "Acima do orçamento"


def spi_color(spi: Optional[float]) -> Optional[str]:
    """Return 'success' / 'warning' / 'danger' for SPI, or None."""
    if spi is None:
        return None
    if spi >= 1.0:
        return "success"
    if spi >= 0.9:
        return "warning"
    return "danger"


def spi_label(spi: Optional[float]) -> Optional[str]:
    """Return human-readable SPI label in pt-BR."""
    if spi is None:
        return None
    if spi >= 1.0:
        return "No prazo"
    if spi >= 0.9:
        return "Atenção"
    return "Atrasado"


def tcpi_color(tcpi: Optional[float]) -> Optional[str]:
    """Return 'success' / 'warning' / 'danger' for TCPI, or None.

    TCPI ≤ 1.0 → achievable (success); ≤ 1.1 → tight (warning); > 1.1 → unreachable (danger).
    """
    if tcpi is None:
        return None
    if tcpi <= 1.0:
        return "success"
    if tcpi <= 1.1:
        return "warning"
    return "danger"


# ── Budget resolution ─────────────────────────────────────────────────────────

def resolve_effective_budget(project, baseline=None) -> tuple[Optional[float], Optional[float]]:
    """Return (budget_hours, budget_cost) — active baseline takes precedence over project fields.

    This is the single rule for which budget is authoritative:
      1. Active baseline (locked, approved revision)
      2. Project fields (initial estimate or manually updated)

    All routers must call this function instead of reading project.budget_* directly.
    """
    bh = (baseline.budget_hours if baseline else None) or (project.budget_hours if project else None)
    bc = (baseline.budget_cost  if baseline else None) or (project.budget_cost  if project else None)
    return bh, bc
