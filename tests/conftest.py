from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.deps import get_current_user
from backend.app.main import app
import backend.app.models  # noqa: F401 — registers all models in Base.metadata
from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord, User

# ---------------------------------------------------------------------------
# Single in-memory engine shared across the entire test session.
# StaticPool ensures every Session uses the same underlying connection so that
# tables created in one session are visible to others.
# ---------------------------------------------------------------------------
_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)


def _override_get_db():
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=_ENGINE)
    yield
    Base.metadata.drop_all(bind=_ENGINE)


_MOCK_ADMIN = User(id=9999, username="test_admin", hashed_password="", role="admin")


@pytest.fixture(scope="session")
def client(create_tables):
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: _MOCK_ADMIN
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Per-test cleanup — wipe all rows between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(create_tables):
    # Wipe before each test so every test starts from a known empty state.
    db = _SessionFactory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield


# ---------------------------------------------------------------------------
# Direct DB session for setup helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Shared model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_cycle(db_session):
    cycle = Cycle(
        name="Jan/2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        is_quarantine=False,
    )
    db_session.add(cycle)
    db_session.commit()
    db_session.refresh(cycle)
    return cycle


@pytest.fixture
def sample_project(db_session):
    project = Project(
        pep_wbs="60OP-03333",
        name="Projeto Teste",
        client="Cliente A",
        manager="Gerente X",
        budget_hours=160.0,
        status="ativo",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_collaborator(db_session):
    collab = Collaborator(name="João Silva")
    db_session.add(collab)
    db_session.commit()
    db_session.refresh(collab)
    return collab


@pytest.fixture
def sample_record(db_session, sample_cycle, sample_collaborator, sample_project):
    record = TimesheetRecord(
        collaborator_id=sample_collaborator.id,
        cycle_id=sample_cycle.id,
        record_date=date(2026, 1, 15),
        pep_wbs=sample_project.pep_wbs,
        pep_description="COPEL-D | OMS",
        normal_hours=8.0,
        extra_hours=0.0,
        standby_hours=0.0,
    )
    db_session.add(record)
    db_session.commit()
    return record
