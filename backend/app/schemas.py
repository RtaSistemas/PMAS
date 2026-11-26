from __future__ import annotations

import math
import re as _re
from datetime import date, date as DateType, datetime
from typing import Annotated, List, Literal, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


# ── Shared validators ────────────────────────────────────────────────────────

_MAX_PASSWORD_BYTES = 72  # bcrypt ignores/rejects anything beyond 72 bytes

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
PepStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
UsernameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100)]


def _blank_to_none(v):
    """Strip optional text fields; blank strings become None."""
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def check_password_value(v: str) -> str:
    if len(v.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise ValueError(f"A senha deve ter no máximo {_MAX_PASSWORD_BYTES} bytes (UTF-8).")
    if "\x00" in v:
        raise ValueError("A senha não pode conter caracteres nulos.")
    return v


# ── Input schemas ────────────────────────────────────────────────────────────

class CycleIn(BaseModel):
    name: NameStr
    start_date: DateType
    end_date: DateType


class ProjectIn(BaseModel):
    pep_wbs: PepStr
    name: Optional[str] = Field(default=None, max_length=200)
    client: Optional[str] = Field(default=None, max_length=200)
    manager: Optional[str] = Field(default=None, max_length=200)
    budget_hours: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    budget_cost: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    status: Literal["ativo", "suspenso", "encerrado"] = "ativo"
    start_date:       Optional[DateType] = None
    planned_end_date: Optional[DateType] = None
    completion_date:  Optional[DateType] = None

    @field_validator("name", "client", "manager", mode="before")
    @classmethod
    def _strip_optional(cls, v):
        return _blank_to_none(v)

    @model_validator(mode="after")
    def _check_dates(self):
        if self.start_date is not None:
            if self.planned_end_date is not None and self.planned_end_date < self.start_date:
                raise ValueError("planned_end_date não pode ser anterior a start_date.")
            if self.completion_date is not None and self.completion_date < self.start_date:
                raise ValueError("completion_date não pode ser anterior a start_date.")
        return self


class ProjectUpdateIn(ProjectIn):
    budget_change_reason: Optional[str] = Field(default=None, max_length=1000)


class SeniorityLevelIn(BaseModel):
    name: NameStr


class RateCardIn(BaseModel):
    seniority_level_id: int
    hourly_rate: float = Field(gt=0, allow_inf_nan=False)
    valid_from: DateType
    valid_to: Optional[DateType] = None


class CollaboratorSeniorityIn(BaseModel):
    seniority_level_id: Optional[int] = None


class ImportResultOut(BaseModel):
    created: int
    updated: int = 0
    errors: List[str] = []
    message: Optional[str] = None


class GlobalConfigIn(BaseModel):
    extra_hours_multiplier: float = Field(gt=0, le=10, allow_inf_nan=False)
    standby_hours_multiplier: float = Field(gt=0, le=10, allow_inf_nan=False)
    anomaly_max_daily_hours: float = Field(default=24.0, gt=0, le=24, allow_inf_nan=False)  # deprecated: use ValidationRule engine
    timezone: str = "America/Sao_Paulo"
    budget_warning_threshold: float = Field(default=0.9, gt=0, le=5, allow_inf_nan=False)
    budget_critical_threshold: float = Field(default=1.0, gt=0, le=5, allow_inf_nan=False)

    @field_validator("timezone")
    @classmethod
    def _check_timezone(cls, v: str) -> str:
        v = v.strip()
        try:
            ZoneInfo(v)
        except Exception:
            raise ValueError(f"Fuso horário desconhecido: '{v}'.")
        return v

    @model_validator(mode="after")
    def _check_thresholds(self):
        if self.budget_warning_threshold >= self.budget_critical_threshold:
            raise ValueError("budget_warning_threshold deve ser menor que budget_critical_threshold.")
        return self


class GlobalConfigOut(BaseModel):
    extra_hours_multiplier: float
    standby_hours_multiplier: float
    anomaly_max_daily_hours: float
    timezone: str
    budget_warning_threshold: float
    budget_critical_threshold: float


class UserCreateIn(BaseModel):
    username: UsernameStr
    password: str = Field(min_length=6)
    role: Literal["admin", "user"] = "user"

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return check_password_value(v)


class PasswordChangeIn(BaseModel):
    new_password: str = Field(min_length=6)
    current_password: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return check_password_value(v)


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
    planned_hours: float = Field(ge=0, allow_inf_nan=False)
    planned_cost: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    physical_pct: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    physical_note: str | None = Field(default=None, max_length=2000)


class ProjectCyclePlanOut(BaseModel):
    id: int
    project_id: int
    cycle_id: int
    cycle_name: str
    planned_hours: float
    planned_cost: float | None = None
    physical_pct: float | None = None
    physical_note: str | None = None


class PhysicalProgressItem(BaseModel):
    cycle_id: int
    physical_pct: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    physical_note: str | None = Field(default=None, max_length=2000)


class ProjectBaselineIn(BaseModel):
    label: Optional[str] = Field(default=None, max_length=200)

    @field_validator("label", mode="before")
    @classmethod
    def _strip_label(cls, v):
        return _blank_to_none(v)


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
    records_summed: int = 0
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


class ValidationRuleBase(BaseModel):
    is_active: bool = True
    order: int = 10
    field: str
    operator: str
    value: Optional[str] = None
    action: str
    description: Optional[str] = None


class ValidationRuleIn(ValidationRuleBase):
    order: int = Field(default=10, ge=1, le=10000)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("field")
    @classmethod
    def _check_field(cls, v: str) -> str:
        if v not in _VALID_RULE_FIELDS:
            raise ValueError(
                f"Campo inválido '{v}'. Permitidos: {sorted(_VALID_RULE_FIELDS)}"
            )
        return v

    @field_validator("operator")
    @classmethod
    def _check_operator(cls, v: str) -> str:
        from backend.app.services.rule_engine import OPERATORS
        if v not in OPERATORS:
            raise ValueError(f"Operador inválido '{v}'. Permitidos: {sorted(OPERATORS)}")
        return v

    @field_validator("action")
    @classmethod
    def _check_action(cls, v: str) -> str:
        from backend.app.services.rule_engine import ACTION_RANK
        if v not in ACTION_RANK:
            raise ValueError(f"Ação inválida '{v}'. Permitidas: {sorted(ACTION_RANK)}")
        return v

    @field_validator("value", mode="before")
    @classmethod
    def _strip_value(cls, v):
        return v.strip() if isinstance(v, str) else v

    @model_validator(mode="after")
    def _check_combination(self):
        _AGGREGATE_FIELDS = {"soma_diaria", "soma_semanal"}
        _AGGREGATE_ACTIONS = {"info", "warning"}
        if self.field in _AGGREGATE_FIELDS and self.action not in _AGGREGATE_ACTIONS:
            raise ValueError("Regras agregadas permitem apenas as ações info ou warning.")
        if self.operator in ("gt", "gte", "lt", "lte"):
            try:
                ok = math.isfinite(float(self.value))
            except (TypeError, ValueError):
                ok = False
            if not ok:
                raise ValueError(f"O operador '{self.operator}' exige um valor numérico.")
        elif self.operator not in ("vazio", "nao_vazio"):
            if self.value is None or not self.value.strip():
                raise ValueError(f"O operador '{self.operator}' exige um valor não vazio.")
        return self


class ValidationRuleOut(ValidationRuleBase):
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

_HEX_COLOR_RE = r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$'
_FONT_FAMILY_RE = r"^[A-Za-z0-9 ,'_.\-]+$"
_DENSITIES = ("compact", "normal", "relaxed")
_BORDER_RADII = ("sharp", "normal", "rounded")
_THEME_COLOR_KEYS = (
    "color_primary", "color_background", "color_surface", "color_accent",
    "color_success", "color_warning", "color_danger", "color_text", "color_text_muted",
    "color_card", "color_border", "color_text_hint", "color_violet",
)
_MAX_APP_NAME = 60
_MAX_FONT_FAMILY = 120


def _check_hex(v: str) -> str:
    if not isinstance(v, str) or not _re.match(_HEX_COLOR_RE, v):
        raise ValueError(f"Cor inválida: {v!r} (esperado #rgb ou #rrggbb).")
    return v


def _check_app_name(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("app_name deve ser texto.")
    v = v.strip()
    if not v:
        raise ValueError("app_name não pode ser vazio.")
    if len(v) > _MAX_APP_NAME:
        raise ValueError(f"app_name deve ter no máximo {_MAX_APP_NAME} caracteres.")
    return v


def _check_font(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ValueError("font_family deve ser texto.")
    v = v.strip()
    if not v:
        return None
    if len(v) > _MAX_FONT_FAMILY:
        raise ValueError(f"font_family deve ter no máximo {_MAX_FONT_FAMILY} caracteres.")
    if not _re.match(_FONT_FAMILY_RE, v):
        raise ValueError("font_family contém caracteres não permitidos.")
    return v


def _check_density(v: str) -> str:
    if v not in _DENSITIES:
        raise ValueError(f"density deve ser um de {list(_DENSITIES)}, recebido {v!r}.")
    return v


def _check_radius(v: Optional[str]) -> Optional[str]:
    if v is not None and v not in _BORDER_RADII:
        raise ValueError(f"border_radius deve ser um de {list(_BORDER_RADII)}, recebido {v!r}.")
    return v


def _check_palette_colors(v: list) -> list:
    if not isinstance(v, list):
        raise ValueError("chart_palette deve ser uma lista de cores.")
    if len(v) > 8:
        raise ValueError("chart_palette deve ter no máximo 8 cores.")
    for color in v:
        _check_hex(color)
    return v


def validate_preset_config(config: dict) -> dict:
    """Validate a theme-preset config with the same rules as UIThemeIn.

    Only known theme keys are kept; None values are allowed for optional keys.
    """
    if not isinstance(config, dict):
        raise ValueError("config deve ser um objeto.")
    out: dict = {}
    for key, val in config.items():
        if key in _THEME_COLOR_KEYS:
            if val is None:
                out[key] = None
            else:
                out[key] = _check_hex(val)
        elif key == "density":
            out[key] = _check_density(val)
        elif key == "border_radius":
            out[key] = _check_radius(val)
        elif key == "chart_palette":
            out[key] = None if val is None else _check_palette_colors(val)
        elif key == "app_name":
            out[key] = _check_app_name(val)
        elif key == "font_family":
            out[key] = _check_font(val)
    return out


class UIThemeIn(BaseModel):
    app_name: str = "PMAS"
    color_primary:    str = "#4f8ef7"
    color_background: str = "#081122"
    color_surface:    str = "#0e2038"
    color_accent:     str = "#07b3d7"
    color_success:    str = "#5ad388"
    color_warning:    str = "#d9b273"
    color_danger:     str = "#c56d76"
    color_text:       str = "#e0e0e0"
    color_text_muted: str = "#818998"
    # New optional tokens
    color_card:       Optional[str] = None  # --card
    color_border:     Optional[str] = None  # --border
    color_text_hint:  Optional[str] = None  # --text-3
    color_violet:     Optional[str] = None  # --violet
    border_radius:    Optional[str] = None  # "sharp" | "normal" | "rounded"
    font_family:      Optional[str] = None
    density: Literal["compact", "normal", "relaxed"] = "normal"
    chart_palette: Optional[List[str]] = Field(default_factory=lambda: [
        "#4f8ef7", "#d9b273", "#a78bfa", "#35a1f3", "#5ad388", "#01c1b9"
    ])

    @field_validator("app_name")
    @classmethod
    def _v_app_name(cls, v: str) -> str:
        return _check_app_name(v)

    @field_validator("font_family")
    @classmethod
    def _v_font(cls, v: Optional[str]) -> Optional[str]:
        return _check_font(v)

    @field_validator(
        "color_primary", "color_background", "color_surface", "color_accent",
        "color_success", "color_warning", "color_danger", "color_text", "color_text_muted",
    )
    @classmethod
    def _check_required_hex(cls, v: str) -> str:
        return _check_hex(v)

    @field_validator("chart_palette")
    @classmethod
    def _check_palette(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None or len(v) == 0:
            return v
        if not (6 <= len(v) <= 8):
            raise ValueError("chart_palette deve ter entre 6 e 8 cores (ou ser vazia).")
        return _check_palette_colors(v)

    @field_validator("color_card", "color_border", "color_text_hint", "color_violet")
    @classmethod
    def _check_optional_hex(cls, v: Optional[str]) -> Optional[str]:
        return None if v is None else _check_hex(v)

    @field_validator("border_radius")
    @classmethod
    def _check_border_radius(cls, v: Optional[str]) -> Optional[str]:
        return _check_radius(v)


class UIThemeOut(UIThemeIn):
    logo_url: Optional[str] = None


# ── Project alerts ────────────────────────────────────────────────────────────

class ProjectAlertOut(BaseModel):
    id: int
    project_id: int
    pep_wbs: str
    alert_type: str
    level: str
    message: str
    metric_value: float | None
    consecutive_cycles: int | None
    created_at: datetime
    resolved_at: datetime | None
    is_resolved: bool
    model_config = ConfigDict(from_attributes=True)


# ── Theme presets ─────────────────────────────────────────────────────────────

class ThemePresetOut(BaseModel):
    id: int
    name: str
    is_builtin: bool
    config: dict
    model_config = ConfigDict(from_attributes=True)


class ThemePresetIn(BaseModel):
    name: NameStr
    config: dict

    @field_validator("config", mode="before")
    @classmethod
    def _check_config(cls, v):
        return validate_preset_config(v)


# ── API keys ─────────────────────────────────────────────────────────────────

class ApiKeyCreateIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=60)]
    user_id: Optional[int] = None          # the user that the key acts as; default = the caller


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    username: str
    created_by: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ApiKeyCreatedOut(ApiKeyOut):
    key: str                               # shown once; the server keeps only a hash
