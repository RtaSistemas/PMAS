from __future__ import annotations

from datetime import date, date as DateType, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ── Input schemas ────────────────────────────────────────────────────────────

class CycleIn(BaseModel):
    name: str
    start_date: DateType
    end_date: DateType


class ProjectIn(BaseModel):
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    budget_hours: Optional[float] = Field(default=None, ge=0)
    budget_cost: Optional[float] = Field(default=None, ge=0)
    status: Literal["ativo", "suspenso", "encerrado"] = "ativo"


class SeniorityLevelIn(BaseModel):
    name: str


class RateCardIn(BaseModel):
    seniority_level_id: int
    hourly_rate: float = Field(gt=0)
    valid_from: DateType
    valid_to: Optional[DateType] = None


class CollaboratorSeniorityIn(BaseModel):
    seniority_level_id: Optional[int] = None


class ImportResultOut(BaseModel):
    created: int
    updated: int = 0
    errors: List[str] = []


class GlobalConfigIn(BaseModel):
    extra_hours_multiplier: float = Field(gt=0)
    standby_hours_multiplier: float = Field(gt=0)


class GlobalConfigOut(BaseModel):
    extra_hours_multiplier: float
    standby_hours_multiplier: float


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=6)
    role: Literal["admin", "user"] = "user"


class PasswordChangeIn(BaseModel):
    new_password: str = Field(min_length=6)
    current_password: Optional[str] = None


# ── Output schemas ───────────────────────────────────────────────────────────

class IdOut(BaseModel):
    id: int


class CycleOut(BaseModel):
    id: int
    name: str
    start_date: DateType
    end_date: DateType
    is_quarantine: bool
    is_closed: bool
    is_active: bool
    record_count: int


class ProjectOut(BaseModel):
    id: int
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    budget_hours: Optional[float] = None
    budget_cost: Optional[float] = None
    status: str


class CollaboratorOut(BaseModel):
    id: int
    name: str


class PepOut(BaseModel):
    code: str
    descriptions: List[str]
    total_records: int


class ProjectCyclePlanIn(BaseModel):
    cycle_id: int
    planned_hours: float = Field(ge=0)


class ProjectCyclePlanOut(BaseModel):
    id: int
    project_id: int
    cycle_id: int
    cycle_name: str
    planned_hours: float


class SeniorityLevelOut(BaseModel):
    id: int
    name: str


class RateCardOut(BaseModel):
    id: int
    seniority_level_id: int
    seniority_level_name: str
    hourly_rate: float
    valid_from: DateType
    valid_to: Optional[DateType] = None


class TeamMemberOut(BaseModel):
    id: int
    name: str
    seniority_level_id: Optional[int] = None
    seniority_level_name: Optional[str] = None
    current_hourly_rate: Optional[float] = None


class SeniorityAssignOut(BaseModel):
    id: int
    seniority_level_id: Optional[int] = None


# Dashboard nested types

class CycleInfo(BaseModel):
    id: Optional[int] = None
    name: str
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    is_quarantine: bool


class DashboardFilters(BaseModel):
    pep_codes: List[str]
    pep_descriptions: List[str]
    collaborator_ids: List[int]


class CollaboratorHours(BaseModel):
    collaborator: str
    normal_hours: float
    extra_hours: float
    standby_hours: float


class BreakdownItem(BaseModel):
    collaborator: str
    pep_code: Optional[str] = None
    pep_description: Optional[str] = None
    normal_hours: float
    extra_hours: float
    standby_hours: float


class BudgetVsActualItem(BaseModel):
    pep_wbs: str
    name: Optional[str] = None
    budget_hours: float
    actual_hours: float


class DashboardOut(BaseModel):
    cycle: CycleInfo
    filters: DashboardFilters
    data: List[CollaboratorHours]
    breakdown: List[BreakdownItem]
    budget_vs_actual: List[BudgetVsActualItem]   # ← última linha atual do DashboardOut
                                                  # ← linha em branco
                                                  # ← linha em branco
class CollaboratorTimelineItem(BaseModel):
    cycle_name: str
    normal_hours: float
    extra_hours: float
    standby_hours: float


# Analytics types

class PortfolioHealthItem(BaseModel):
    pep_wbs: str
    pep_description: Optional[str] = None
    name: Optional[str] = None
    budget_hours: Optional[float] = None
    budget_cost: Optional[float] = None
    consumed_hours: float
    actual_cost: float
    is_registered: bool


class TrendItem(BaseModel):
    cycle_name: str
    normal_hours: float
    extra_hours: float
    standby_hours: float
    actual_cost: float
    cpi: float | None = None


class AllocationItem(BaseModel):
    collaborator: str
    pep_wbs: str | None
    pep_description: str | None
    total_hours: float
    actual_cost: float


class BurnHistoryPoint(BaseModel):
    cycle_name: str
    cycle_start: date
    period_hours: float
    period_cost: float
    cumulative_hours: float
    cumulative_cost: float
    planned_hours: float | None = None
    cumulative_planned_hours: float | None = None


class ForecastOut(BaseModel):
    pep_wbs: str
    pep_description: str | None
    budget_hours: float | None
    budget_cost: float | None
    consumed_hours: float
    actual_cost: float
    remaining_hours: float | None
    cpi: float | None
    eac: float | None
    spi: float | None = None
    sv: float | None = None
    avg_hours_per_cycle: float
    estimated_cycles_to_complete: float | None
    estimated_completion_cycle: str | None
    history: list[BurnHistoryPoint]


class UploadOut(BaseModel):
    status: str
    records_inserted: int
    records_skipped: int
    quarantine_cycles_created: int
    warnings: List[str] = []


class PepRadarItem(BaseModel):
    pep_description: str
    total_hours: float
    actual_cost: float


# Auth

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    role: str


class AuditLogItem(BaseModel):
    id: int
    username: str | None
    action: str
    entity: str
    entity_id: int | None
    detail: str | None
    timestamp: datetime
