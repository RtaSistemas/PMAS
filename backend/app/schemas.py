from __future__ import annotations

from datetime import date, date as DateType, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    manager_id: Optional[int] = None
    budget_hours: Optional[float] = Field(default=None, ge=0)
    budget_cost: Optional[float] = Field(default=None, ge=0)
    status: Literal["ativo", "suspenso", "encerrado"] = "ativo"
    start_date:       Optional[DateType] = None
    planned_end_date: Optional[DateType] = None
    completion_date:  Optional[DateType] = None


class ProjectUpdateIn(ProjectIn):
    budget_change_reason: Optional[str] = None


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
    anomaly_max_daily_hours: float = Field(default=24.0, gt=0)  # deprecated: use ValidationRule engine
    timezone: str = "America/Sao_Paulo"
    budget_warning_threshold: float = Field(default=0.9, gt=0, le=1)
    budget_critical_threshold: float = Field(default=1.0, gt=0, le=2)


class GlobalConfigOut(BaseModel):
    extra_hours_multiplier: float
    standby_hours_multiplier: float
    anomaly_max_daily_hours: float
    timezone: str
    budget_warning_threshold: float
    budget_critical_threshold: float


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
    is_closed: bool
    is_active: bool
    record_count: int


class ProjectOut(BaseModel):
    id: int
    pep_wbs: str
    name: Optional[str] = None
    client: Optional[str] = None
    manager: Optional[str] = None
    manager_id: Optional[int] = None
    budget_hours: Optional[float] = None
    budget_cost: Optional[float] = None
    status: str
    start_date:       Optional[DateType] = None
    planned_end_date: Optional[DateType] = None
    completion_date:  Optional[DateType] = None


class UserProjectAccessIn(BaseModel):
    user_id: int


class UserProjectAccessOut(BaseModel):
    id: int
    user_id: int
    username: str
    project_id: int
    pep_wbs: str


class ProjectCyclePlanIn(BaseModel):
    cycle_id: int
    planned_hours: float = Field(ge=0)
    planned_cost: float | None = Field(default=None, ge=0)


class ProjectCyclePlanOut(BaseModel):
    id: int
    project_id: int
    cycle_id: int
    cycle_name: str
    planned_hours: float
    planned_cost: float | None = None


class ProjectBaselineIn(BaseModel):
    label: Optional[str] = None


class ProjectBaselineOut(BaseModel):
    id: int
    project_id: int
    locked_at: datetime
    locked_by: Optional[str] = None
    budget_hours: Optional[float] = None
    budget_cost: Optional[float] = None
    label: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class BudgetRevisionOut(BaseModel):
    id: int
    project_id: int
    old_budget_hours: Optional[float] = None
    old_budget_cost: Optional[float] = None
    new_budget_hours: Optional[float] = None
    new_budget_cost: Optional[float] = None
    reason: Optional[str] = None
    changed_by: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


class CollaboratorTimelineItem(BaseModel):
    cycle_name: str
    cycle_start: str
    normal_hours: float
    extra_hours: float
    standby_hours: float


class UploadOut(BaseModel):
    status: str
    records_inserted: int
    records_skipped: int
    quarantine_records_added: int = 0
    warning_count: int = 0
    info_count: int = 0
    warnings: List[str] = []
    infos: List[str] = []
    upload_session_id: Optional[int] = None


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

    model_config = ConfigDict(from_attributes=True)


# ── Validation rules ─────────────────────────────────────────────────────────

_VALID_RULE_FIELDS = {
    "horas_individuais", "hora_extra", "hora_sobreaviso",
    "hora_extra_horas", "hora_sobreaviso_horas",
    "pep_wbs", "dia_semana", "soma_diaria", "soma_semanal",
}


class ValidationRuleIn(BaseModel):
    is_active: bool = True
    order: int = Field(default=10, ge=1)
    field: str
    operator: str
    value: Optional[str] = None
    action: str
    description: Optional[str] = None

    @field_validator("field")
    @classmethod
    def _check_field(cls, v: str) -> str:
        if v not in _VALID_RULE_FIELDS:
            raise ValueError(
                f"Campo inválido '{v}'. Permitidos: {sorted(_VALID_RULE_FIELDS)}"
            )
        return v

    def model_post_init(self, __context) -> None:
        _AGGREGATE_FIELDS = {"soma_diaria", "soma_semanal"}
        _AGGREGATE_ACTIONS = {"info", "warning"}
        if self.field in _AGGREGATE_FIELDS and self.action not in _AGGREGATE_ACTIONS:
            raise ValueError("Aggregate rules allow only info or warning.")


class ValidationRuleOut(ValidationRuleIn):
    id: int
    is_system: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Quarantine ───────────────────────────────────────────────────────────────

class QuarantineRecordOut(BaseModel):
    id: int
    ingested_at: datetime
    upload_session_id: Optional[int] = None
    uploaded_by_username: Optional[str] = None
    raw_data: Optional[dict] = None
    quarantine_reason: str
    rule_id: Optional[int] = None
    rule_description: Optional[str] = None
    reviewed: bool
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_status: str = "pending"

    model_config = ConfigDict(from_attributes=True)


class QuarantineReviewIn(BaseModel):
    reviewed: bool


# ── Upload session ───────────────────────────────────────────────────────────

class UploadSessionOut(BaseModel):
    id: int
    uploaded_at: datetime
    uploaded_by_username: str
    source_file: str
    records_inserted: int
    records_skipped: int
    quarantine_added: int
    warning_count: int
    info_count: int
    status: str
    warnings_detail: Optional[List[str]] = None
    infos_detail: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# ── Alert summary ────────────────────────────────────────────────────────────

class AlertSummaryOut(BaseModel):
    message: str
    occurrences: int
    last_triggered: datetime
    trend: str  # up | down | stable


# ── User preferences ─────────────────────────────────────────────────────────

class UserPreferenceIn(BaseModel):
    dashboard: Optional[dict] = None


class UserPreferenceOut(BaseModel):
    user_id: int
    dashboard: Optional[dict] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── UI theme ─────────────────────────────────────────────────────────────────

class UIThemeIn(BaseModel):
    app_name: str = "PMAS"
    color_primary: str = "#4f8ef7"
    color_background: str = "#081122"
    color_surface: str = "#0e2038"
    color_accent: str = "#07b3d7"
    color_success: str = "#5ad388"
    color_warning: str = "#d9b273"
    color_danger: str = "#c56d76"
    color_text: str = "#e0e0e0"
    color_text_muted: str = "#818998"
    density: Literal["compact", "normal", "relaxed"] = "normal"
    chart_palette: List[str] = Field(default_factory=lambda: [
        "#4f8ef7", "#d9b273", "#a78bfa", "#35a1f3", "#5ad388", "#01c1b9"
    ])


class UIThemeOut(UIThemeIn):
    logo_url: Optional[str] = None


# ── Theme presets ─────────────────────────────────────────────────────────────

class ThemePresetOut(BaseModel):
    id: int
    name: str
    is_builtin: bool
    config: dict
    model_config = ConfigDict(from_attributes=True)


class ThemePresetIn(BaseModel):
    name: str
    config: dict


