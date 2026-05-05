from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


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
    is_quarantine = Column(Boolean, default=False, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    records = relationship("TimesheetRecord", back_populates="cycle")


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
    cycle = relationship("Cycle")

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


class GlobalConfig(Base):
    __tablename__ = "global_config"

    id = Column(Integer, primary_key=True)          # singleton — always id=1
    extra_hours_multiplier = Column(Float, default=1.5, nullable=False)
    standby_hours_multiplier = Column(Float, default=1.0, nullable=False)
    anomaly_max_daily_hours = Column(Float, default=24.0, nullable=False)


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
