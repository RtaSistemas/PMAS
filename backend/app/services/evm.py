"""EVM calculation functions — single source of truth.

Every EVM metric (CPI, SPI, EAC, EV, …) must be computed through
a function defined here.  No other file may re-implement these formulas.
"""
from __future__ import annotations

from typing import Optional, Tuple


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
    ev_cost: Optional[float],
    actual_cost: float,
) -> Optional[float]:
    """Cost Performance Index = EV / AC.

    Pass true Earned Value (e.g. from compute_ev_capped), not BAC.
    Using BAC as EV is only valid for a 100% complete project.
    Returns None when actual_cost == 0 or ev_cost is undefined.
    > 1.0 → under budget;  < 1.0 → over budget.
    """
    if not ev_cost or actual_cost == 0:
        return None
    return round(ev_cost / actual_cost, 4)


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
    """Schedule Performance Index — AgileEVM hours proxy: actual_h / planned_h.

    This implementation uses hours rather than monetary EV/PV (AgileEVM proxy).
    Both methods converge when work cost is uniformly distributed; the hours
    proxy is preferable when only hours baselines are available.

    Returns None when planned hours are undefined or zero.
    > 1.0 → ahead of schedule;  < 1.0 → behind.
    """
    if not cumulative_planned_hours or cumulative_planned_hours == 0:
        return None
    return round(cumulative_actual_hours / cumulative_planned_hours, 4)


def compute_eac(
    budget_cost: Optional[float],
    cpi: Optional[float],
    *,
    default_to_bac: bool = False,
) -> Optional[float]:
    """Estimate at Completion = BAC / CPI.

    When cpi is None or 0 and default_to_bac is True, returns BAC as the
    baseline projection (i.e. no performance divergence observed yet).
    """
    if not budget_cost:
        return None
    if not cpi or cpi == 0:
        return round(budget_cost, 2) if default_to_bac else None
    return round(budget_cost / cpi, 2)


def compute_eac_schedule(
    budget_cost: Optional[float],
    actual_cost: float,
    ev_cost: Optional[float],
    cpi: Optional[float],
    spi: Optional[float],
) -> Optional[float]:
    """Schedule-sensitive Estimate at Completion: AC + (BAC − EV) / (CPI × SPI).

    Accounts for both cost and schedule performance when projecting total cost.
    Useful when SPI < 1 (behind schedule), as it raises the cost forecast.
    Returns None when any required input is missing or CPI×SPI ≤ 0.
    """
    if not budget_cost or ev_cost is None or not cpi or not spi or cpi <= 0 or spi <= 0:
        return None
    combined = cpi * spi
    return round(actual_cost + (budget_cost - ev_cost) / combined, 2)


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


def compute_etc(
    eac: Optional[float],
    actual_cost: Optional[float],
) -> Optional[float]:
    """Estimate to Complete = EAC − AC, zero-floored."""
    if eac is None or actual_cost is None:
        return None
    return round(max(eac - actual_cost, 0.0), 2)


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
    """Earned Value in R$ using the blended planned rate (uncapped).

    EV = cumulative_hours × (budget_cost / budget_hours)

    NOTE: this function does NOT cap EV at BAC.  For the burn-up chart and
    for CPI/EAC calculations use compute_ev_capped, which limits EV to BAC.
    This function is kept for diagnostic/raw-series use only.
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

    Returns one of: 'ok' | 'warning' | 'overrun' | 'no_budget'.
    """
    if not budget or budget == 0:
        return "no_budget"
    ratio = consumed / budget
    if ratio >= critical_threshold:
        return "overrun"
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


# ── Freeze SPI at last plan boundary ─────────────────────────────────────────

def freeze_spi_boundary(
    actual_series: list,
    plan_series: list,
) -> tuple:
    """Return (last_actual_h, last_planned_h) frozen at the last plan-advance boundary.

    actual_series: [(cycle_start, period_hours), ...] — sorted internally, accumulated.
    plan_series:   [(cycle_start, period_planned_hours), ...] — cumulative built inside.

    Walks actual cycles in chronological order and tracks the last cycle where
    cumulative planned hours increased.  The returned pair is used to compute
    a frozen SPI/SV that does not drift after the last planned cycle ends.

    Returns (None, None) when the plan never advances past zero.
    """
    plan_sorted = sorted(plan_series)
    cum_actual = 0.0
    prev_cum_ph = 0.0
    last_actual_h: Optional[float] = None
    last_planned_h: Optional[float] = None

    for c_start, period_h in sorted(actual_series):
        cum_actual += period_h
        cum_ph = sum(h for s, h in plan_sorted if s <= c_start)
        if cum_ph > prev_cum_ph:
            last_actual_h = cum_actual
            last_planned_h = cum_ph
            prev_cum_ph = cum_ph

    return last_actual_h, last_planned_h


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


def tcpi_label(tcpi: Optional[float]) -> Optional[str]:
    """Human-readable TCPI label in pt-BR."""
    if tcpi is None:
        return None
    if tcpi <= 1.0:
        return "Meta alcançável"
    if tcpi <= 1.1:
        return "Meta apertada"
    return "Meta inviável no ritmo atual"


# ── Schedule status ───────────────────────────────────────────────────────────

def classify_schedule_status(
    spi: Optional[float],
    warning_threshold: float = 0.9,
) -> str:
    """Classify SPI into 'on_track' | 'at_risk' | 'behind' | 'no_baseline'."""
    if spi is None:
        return "no_baseline"
    if spi >= 1.0:
        return "on_track"
    if spi >= warning_threshold:
        return "at_risk"
    return "behind"


# ── Concentration risk ────────────────────────────────────────────────────────

def classify_concentration_risk(
    top1_pct: float,
    high_threshold: float = 60.0,
    medium_threshold: float = 40.0,
) -> str:
    """Classify dependency on the top contributor: 'high' | 'medium' | 'low'."""
    if top1_pct >= high_threshold:
        return "high"
    if top1_pct >= medium_threshold:
        return "medium"
    return "low"


# ── SV / CV labels and colors ─────────────────────────────────────────────────

def sv_label(sv: Optional[float]) -> Optional[str]:
    """Human-readable Schedule Variance label in pt-BR."""
    if sv is None:
        return None
    if sv > 0:
        return f"Adiantado em {abs(sv):.1f}h"
    if sv < 0:
        return f"Atrasado em {abs(sv):.1f}h"
    return "No prazo"


def sv_color(sv: Optional[float], warning_threshold: float = -10.0) -> Optional[str]:
    """Return 'success' / 'warning' / 'danger' for Schedule Variance."""
    if sv is None:
        return None
    if sv >= 0:
        return "success"
    if sv >= warning_threshold:
        return "warning"
    return "danger"


def cv_label(cv: Optional[float]) -> Optional[str]:
    """Human-readable Cost Variance label in pt-BR."""
    if cv is None:
        return None
    if cv > 0:
        return f"Economia de R$ {abs(cv):,.2f}"
    if cv < 0:
        return f"Estouro de R$ {abs(cv):,.2f}"
    return "No orçamento"


def cv_color(cv: Optional[float]) -> Optional[str]:
    """Return 'success' / 'danger' for Cost Variance."""
    if cv is None:
        return None
    return "success" if cv >= 0 else "danger"


def vac_label(vac: Optional[float]) -> Optional[str]:
    """Human-readable VAC label in pt-BR."""
    if vac is None:
        return None
    if vac > 0:
        return "Economia projetada"
    if vac < 0:
        return "Estouro projetado"
    return "No orçamento"


def vac_color(vac: Optional[float]) -> Optional[str]:
    """Return 'success' / 'danger' for Variance at Completion, or None."""
    if vac is None:
        return None
    return "success" if vac >= 0 else "danger"


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


# ── Earned Schedule (F3) ──────────────────────────────────────────────────────

def compute_earned_schedule(
    cumulative_ev_cost: Optional[float],
    pv_cost_curve: list[float],
) -> Optional[float]:
    """Interpolate ES: the fractional time-unit at which EV == cumulative PV.

    pv_cost_curve is a list of cumulative PV values ordered by cycle (0-based).
    Returns None if inputs are insufficient.
    """
    if not pv_cost_curve or cumulative_ev_cost is None or cumulative_ev_cost <= 0:
        return None
    if cumulative_ev_cost >= pv_cost_curve[-1]:
        return float(len(pv_cost_curve))
    for i in range(len(pv_cost_curve)):
        pv_at_t = pv_cost_curve[i]
        pv_prev = pv_cost_curve[i - 1] if i > 0 else 0.0
        if cumulative_ev_cost <= pv_at_t:
            if pv_at_t == pv_prev:
                return float(i)
            frac = (cumulative_ev_cost - pv_prev) / (pv_at_t - pv_prev)
            return round(i + frac, 4)
    return float(len(pv_cost_curve))


def compute_spi_t(
    earned_schedule: Optional[float],
    actual_time: float,
) -> Optional[float]:
    """SPI(t) = ES / AT.  Returns None if inputs are missing or AT is zero."""
    if earned_schedule is None or actual_time <= 0:
        return None
    return round(earned_schedule / actual_time, 4)


def compute_sv_t(
    earned_schedule: Optional[float],
    actual_time: float,
) -> Optional[float]:
    """SV(t) = ES - AT.  Negative means behind schedule (in cycle units)."""
    if earned_schedule is None:
        return None
    return round(earned_schedule - actual_time, 2)


def compute_ieac_t(
    planned_duration: Optional[float],
    spi_t: Optional[float],
) -> Optional[float]:
    """IEAC(t) = PD / SPI(t).  Independent EAC in time units."""
    if planned_duration is None or spi_t is None or spi_t == 0:
        return None
    return round(planned_duration / spi_t, 2)


# ── GlobalConfig threshold helper ────────────────────────────────────────────

def get_thresholds(cfg) -> Tuple[float, float]:
    """Return (warning_threshold, critical_threshold) from a GlobalConfig row.

    Falls back to 0.9 / 1.0 when cfg is None or the columns are absent.
    This is the single source of truth for budget threshold defaults.
    """
    warning  = getattr(cfg, 'budget_warning_threshold',  None) if cfg else None
    critical = getattr(cfg, 'budget_critical_threshold', None) if cfg else None
    return (warning if warning is not None else 0.9,
            critical if critical is not None else 1.0)
