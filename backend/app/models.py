from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base
from backend.app.utils import now_br


class SeniorityLevel(Base):
    __tablename__ = "seniority_level"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    rate_cards = relationship("RateCard", back_populates="seniority_level", cascade="all, delete-orphan")
    collaborators = relationship("Collaborator", back_populates="seniority_level")


class RateCard(Base):
    __tablename__ = "rate_card"

    id = Column(Integer, primary_key=True, index=True)
    seniority_level_id = Column(Integer, ForeignKey("seniority_level.id"), nullable=False)
    hourly_rate = Column(Float, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)

    seniority_level = relationship("SeniorityLevel", back_populates="rate_cards")


class Collaborator(Base):
    __tablename__ = "collaborator"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    seniority_level_id = Column(Integer, ForeignKey("seniority_level.id"), nullable=True)

    records = relationship("TimesheetRecord", back_populates="collaborator")
    seniority_level = relationship("SeniorityLevel", back_populates="collaborators")


class Cycle(Base):
    __tablename__ = "cycle"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    records = relationship("TimesheetRecord", back_populates="cycle")
    project_plans = relationship("ProjectCyclePlan", back_populates="cycle")


class TimesheetRecord(Base):
    __tablename__ = "timesheet_record"

    id = Column(Integer, primary_key=True, index=True)
    collaborator_id = Column(Integer, ForeignKey("collaborator.id"), nullable=False)
    cycle_id = Column(Integer, ForeignKey("cycle.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    pep_wbs = Column(String, nullable=True, index=True)
    pep_description = Column(String, nullable=True, index=True)
    normal_hours = Column(Float, default=0.0, nullable=False)
    extra_hours = Column(Float, default=0.0, nullable=False)
    standby_hours = Column(Float, default=0.0, nullable=False)
    cost_per_hour = Column(Float, default=0.0, nullable=False)

    collaborator = relationship("Collaborator", back_populates="records")
    cycle = relationship("Cycle", back_populates="records")


Index(
    "ix_timesheet_cycle_collaborator",
    TimesheetRecord.cycle_id,
    TimesheetRecord.collaborator_id,
)


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    pep_wbs = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    client = Column(String, nullable=True)
    manager = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    budget_hours = Column(Float, nullable=True)
    budget_cost = Column(Float, nullable=True)
    # ativo | encerrado | suspenso
    status = Column(String, default="ativo", nullable=False)

    plans = relationship("ProjectCyclePlan", back_populates="project", cascade="all, delete-orphan")
    user_access = relationship("UserProjectAccess", back_populates="project", cascade="all, delete-orphan")
    manager_user = relationship("User", foreign_keys=[manager_id], back_populates="managed_projects")


class ProjectCyclePlan(Base):
    __tablename__ = "project_cycle_plan"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    cycle_id = Column(Integer, ForeignKey("cycle.id", ondelete="CASCADE"), nullable=False)
    planned_hours = Column(Float, nullable=False)

    project = relationship("Project", back_populates="plans")
    cycle = relationship("Cycle", back_populates="project_plans")

    __table_args__ = (
        Index("ix_project_cycle_plan_unique", "project_id", "cycle_id", unique=True),
    )


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")

    managed_projects = relationship("Project", foreign_keys="Project.manager_id", back_populates="manager_user")
    project_access = relationship("UserProjectAccess", back_populates="user", cascade="all, delete-orphan")
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")


class GlobalConfig(Base):
    __tablename__ = "global_config"

    id = Column(Integer, primary_key=True)          # singleton — always id=1
    extra_hours_multiplier = Column(Float, default=1.5, nullable=False)
    standby_hours_multiplier = Column(Float, default=0.33, nullable=False)
    anomaly_max_daily_hours = Column(Float, default=24.0, nullable=False)
    timezone = Column(String, nullable=False, default="America/Sao_Paulo")
    ui_theme = Column(JSON, nullable=True)
    logo_path = Column(String, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    username  = Column(String, nullable=True)
    action    = Column(String, nullable=False)
    entity    = Column(String, nullable=False, index=True)
    entity_id = Column(Integer, nullable=True)
    detail    = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)


class UserProjectAccess(Base):
    """Explicit ACL: delegates upload permission on a project to a user."""
    __tablename__ = "user_project_access"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("user.id",    ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)

    user    = relationship("User",    back_populates="project_access")
    project = relationship("Project", back_populates="user_access")

    __table_args__ = (
        Index("ix_user_project_access_unique", "user_id", "project_id", unique=True),
    )


class ValidationRule(Base):
    __tablename__ = "validation_rule"

    id          = Column(Integer, primary_key=True, index=True)
    is_active   = Column(Boolean, default=True, nullable=False, index=True)
    is_system   = Column(Boolean, default=False, nullable=False)
    order       = Column(Integer, default=10, nullable=False, index=True)
    field       = Column(String, nullable=False)
    operator    = Column(String, nullable=False)
    value       = Column(String, nullable=True)
    action      = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by  = Column(String, nullable=True)
    created_at  = Column(DateTime, nullable=False, default=now_br)
    updated_by  = Column(String, nullable=True)
    updated_at  = Column(DateTime, nullable=True)

    quarantine_records = relationship("QuarantineRecord", back_populates="rule")


class UploadSession(Base):
    __tablename__ = "upload_session"

    id                   = Column(Integer, primary_key=True, index=True)
    uploaded_at          = Column(DateTime, nullable=False, default=now_br, index=True)
    uploaded_by_user_id  = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_username = Column(String, nullable=False)
    source_file          = Column(String, nullable=False)
    records_inserted     = Column(Integer, default=0, nullable=False)
    records_skipped      = Column(Integer, default=0, nullable=False)
    quarantine_added     = Column(Integer, default=0, nullable=False)
    warning_count        = Column(Integer, default=0, nullable=False)
    info_count           = Column(Integer, default=0, nullable=False)
    status               = Column(String, nullable=False)
    warnings_detail      = Column(JSON, nullable=True)
    infos_detail         = Column(JSON, nullable=True)

    quarantine_records = relationship("QuarantineRecord", back_populates="upload_session")

    __table_args__ = (
        Index("ix_upload_session_user_at", "uploaded_by_user_id", "uploaded_at"),
    )


class QuarantineRecord(Base):
    __tablename__ = "quarantine_record"

    id                   = Column(Integer, primary_key=True, index=True)
    ingested_at          = Column(DateTime, nullable=False, default=now_br)
    upload_session_id    = Column(Integer, ForeignKey("upload_session.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_user_id  = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_username = Column(String, nullable=True)
    raw_data             = Column(JSON, nullable=True)
    quarantine_reason    = Column(String, nullable=False)
    rule_id              = Column(Integer, ForeignKey("validation_rule.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed             = Column(Boolean, default=False, nullable=False, index=True)
    reviewed_by          = Column(String, nullable=True)
    reviewed_at          = Column(DateTime, nullable=True)
    review_status        = Column(String, default="pending", nullable=False)

    upload_session = relationship("UploadSession", back_populates="quarantine_records")
    rule           = relationship("ValidationRule", back_populates="quarantine_records")

    @property
    def rule_description(self) -> str | None:
        if self.rule:
            return self.rule.description
        return None


class UserPreference(Base):
    __tablename__ = "user_preference"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    dashboard  = Column(JSON, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="preference")
