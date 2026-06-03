"""GET /api/v2/projects/{project_id}/monte-carlo — Monte Carlo Simulation (F4).

Runs N iterations of a cycle-based completion simulation drawing
random velocities from a Gaussian fitted to historical cycle data,
returning P10 / P50 / P90 percentile cycle counts.
"""
from __future__ import annotations

import math
import random
import statistics
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Project, ProjectBaseline
from backend.app.routers.v2.forecast import _load_cycle_data
from backend.app.services.evm import resolve_effective_budget

router = APIRouter(prefix="/api/v2", tags=["v2"])


class MonteCarloOut:
    """Plain dataclass — returned as dict by the endpoint."""


@router.get(
    "/projects/{project_id}/monte-carlo",
    summary="Monte Carlo Simulation — distribuição de ciclos para conclusão",
)
def monte_carlo(
    project_id: int,
    db: DbSession,
    current_user=Depends(get_current_user),
    iterations: int = Query(default=1000, ge=1, le=10000),
    date_from: Optional[DateType] = None,
    date_to: Optional[DateType] = None,
    seed: Optional[int] = None,
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    active_baseline = (
        db.query(ProjectBaseline)
        .filter_by(project_id=project_id, is_active=True)
        .first()
    )
    budget_hours, _ = resolve_effective_budget(project, active_baseline)

    cycle_data = _load_cycle_data(db, project.pep_wbs, date_from, date_to)

    consumed_hours = sum(h for _, _, h, _ in cycle_data)
    remaining = max(0.0, (budget_hours or 0.0) - consumed_hours)

    velocities = [h for _, _, h, _ in cycle_data if h > 0]

    insufficient = {
        "p10": None,
        "p50": None,
        "p90": None,
        "mean_velocity": None,
        "stdev_velocity": None,
        "consumed_hours": round(consumed_hours, 2),
        "remaining_hours": round(remaining, 2),
        "budget_hours": budget_hours,
        "iterations": iterations,
        "error": "insufficient_data",
    }

    if len(velocities) < 2:
        return insufficient

    mu    = statistics.mean(velocities)
    sigma = statistics.stdev(velocities)

    # Handle the trivial case where work is already done
    if remaining <= 0:
        return {
            "p10": 0,
            "p50": 0,
            "p90": 0,
            "mean_velocity": round(mu, 2),
            "stdev_velocity": round(sigma, 2),
            "consumed_hours": round(consumed_hours, 2),
            "remaining_hours": 0.0,
            "budget_hours": budget_hours,
            "iterations": iterations,
            "error": None,
        }

    if seed is not None:
        random.seed(seed)

    results: list[int] = []
    max_cycles = 500
    for _ in range(iterations):
        total = 0.0
        cycles = 0
        while total < remaining and cycles < max_cycles:
            v = max(0.01, random.gauss(mu, sigma))
            total += v
            cycles += 1
        results.append(cycles)

    results.sort()
    n = len(results)
    p10 = results[int(0.10 * n)]
    p50 = results[int(0.50 * n)]
    p90 = results[int(0.90 * n)]

    # Build histogram buckets for frontend chart
    min_r, max_r = results[0], results[-1]
    if max_r - min_r <= 30:
        from collections import Counter
        counts = Counter(results)
        histogram = [{"cycle": k, "count": counts[k]} for k in range(min_r, max_r + 1)]
    else:
        from collections import Counter
        n_buckets = 20
        width = math.ceil((max_r - min_r + 1) / n_buckets)
        counts = Counter(results)
        histogram = []
        for i in range(n_buckets):
            lo = min_r + i * width
            hi = min_r + (i + 1) * width
            cnt = sum(counts.get(k, 0) for k in range(lo, hi))
            histogram.append({"cycle": lo, "count": cnt})

    return {
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "mean_velocity": round(mu, 2),
        "stdev_velocity": round(sigma, 2),
        "consumed_hours": round(consumed_hours, 2),
        "remaining_hours": round(remaining, 2),
        "budget_hours": budget_hours,
        "iterations": iterations,
        "histogram": histogram,
        "error": None,
    }
