"""POST /api/v2/projects/{project_id}/simulate — What-If Simulation (F11).

Given a project ID and scenario parameters (velocity multiplier,
extra hours per cycle), projects how many cycles remain to complete
the project and what the estimated cost at completion will be.
"""
from __future__ import annotations

import math
import statistics
from datetime import date as DateType
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.database import DbSession
from backend.app.deps import get_current_user
from backend.app.models import Project, ProjectBaseline
from backend.app.routers.v2.forecast import _load_cycle_data
from backend.app.services.evm import compute_eac_avg_rate, resolve_effective_budget

router = APIRouter(prefix="/api/v2", tags=["v2"])


class SimulateIn(BaseModel):
    velocity_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    extra_hours_per_cycle: float = Field(default=0.0, ge=0)
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None


class SimulateOut(BaseModel):
    consumed_hours: float
    consumed_cost: float
    remaining_hours: float
    avg_velocity: float           # historical avg hours/cycle
    sim_velocity: float           # effective velocity in scenario
    cycles_to_complete: Optional[int]
    budget_hours: Optional[float]
    budget_cost: Optional[float]
    projected_eac_cost: Optional[float]
    burn_up_projected: list[float]  # cumulative hours each projected cycle


@router.post(
    "/projects/{project_id}/simulate",
    response_model=SimulateOut,
    summary="What-If Simulation — projeção de velocidade e custo ao término",
)
def simulate_project(
    project_id: int,
    body: SimulateIn,
    db: DbSession,
    current_user=Depends(get_current_user),
) -> SimulateOut:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    active_baseline = (
        db.query(ProjectBaseline)
        .filter_by(project_id=project_id, is_active=True)
        .first()
    )
    budget_hours, budget_cost = resolve_effective_budget(project, active_baseline)

    cycle_data = _load_cycle_data(db, project.pep_wbs, body.date_from, body.date_to)

    consumed_hours = sum(h for _, _, h, _ in cycle_data)
    consumed_cost  = sum(c for _, _, _, c in cycle_data)
    remaining      = max(0.0, (budget_hours or 0.0) - consumed_hours)

    # VELOCITY WINDOW — last min(6, N) cycles (Simulate rule).
    # Wider than Forecast/Runway (3 cycles) intentionally: the What-If tool is
    # used for scenario planning, where a smoother baseline is preferable to
    # one that over-reacts to a single atypical cycle.  The user then applies
    # a multiplier on top, so sensitivity is controlled explicitly.
    # Does NOT exclude zero-hour cycles — they represent real idle periods and
    # should deflate the average when present.
    # Compare: Forecast/Runway use 3 cycles; Monte Carlo uses ALL non-zero cycles.
    n = min(6, len(cycle_data))
    if n > 0:
        velocities = [h for _, _, h, _ in cycle_data[-n:]]
        avg_velocity = statistics.mean(velocities) if velocities else 0.0
    else:
        avg_velocity = 0.0

    # Apply scenario
    sim_velocity = avg_velocity * body.velocity_multiplier + body.extra_hours_per_cycle

    # Cycles to complete
    if sim_velocity <= 0:
        cycles_to_complete = None
    elif remaining > 0:
        cycles_to_complete = math.ceil(remaining / sim_velocity)
    else:
        cycles_to_complete = 0

    # Build projected burn-up
    burn_up_projected: list[float] = []
    if cycles_to_complete is not None and cycles_to_complete > 0:
        for i in range(cycles_to_complete):
            projected = consumed_hours + (i + 1) * sim_velocity
            if budget_hours is not None:
                projected = min(projected, budget_hours)
            burn_up_projected.append(round(projected, 2))

    # Projected EAC cost — delegates to the canonical formula in evm.py (GR-2).
    projected_eac_cost = compute_eac_avg_rate(consumed_cost, consumed_hours, remaining)

    return SimulateOut(
        consumed_hours=round(consumed_hours, 2),
        consumed_cost=round(consumed_cost, 2),
        remaining_hours=round(remaining, 2),
        avg_velocity=round(avg_velocity, 2),
        sim_velocity=round(sim_velocity, 2),
        cycles_to_complete=cycles_to_complete,
        budget_hours=budget_hours,
        budget_cost=budget_cost,
        projected_eac_cost=projected_eac_cost,
        burn_up_projected=burn_up_projected,
    )
