from __future__ import annotations

from datetime import date as DateType
from typing import Optional

from pydantic import BaseModel


class CycleIn(BaseModel):
    name: str
    start_date: DateType
    end_date: DateType


class ProjectIn(BaseModel):
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    budget_hours: Optional[float] = None
    budget_cost: Optional[float] = None
    status: str = "ativo"


class SeniorityLevelIn(BaseModel):
    name: str


class RateCardIn(BaseModel):
    seniority_level_id: int
    hourly_rate: float
    valid_from: DateType
    valid_to: Optional[DateType] = None


class CollaboratorSeniorityIn(BaseModel):
    seniority_level_id: Optional[int] = None
