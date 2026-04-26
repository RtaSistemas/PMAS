from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
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
    budget_hours = Column(Float, nullable=True)
    budget_cost = Column(Float, nullable=True)
    # ativo | encerrado | suspenso
    status = Column(String, default="ativo", nullable=False)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
