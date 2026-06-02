"""Tests for GET /api/v2/over-allocation.

The over-allocation router is tested via a local FastAPI app that includes
only the required routers (the router is not yet wired into main.py).
Auth is overridden via dependency_overrides.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401 — ensure all models are registered
from backend.app.database import Base, get_db
from backend.app.deps import get_current_user
from backend.app.models import (
    Collaborator, Cycle, GlobalConfig, TimesheetRecord, User,
    ValidationRule,
)
from backend.app.routers.v2.over_allocation import router as over_allocation_router

# ---------------------------------------------------------------------------
# Isolated in-memory DB + mini FastAPI app for this test module
# ---------------------------------------------------------------------------

_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)

Base.metadata.create_all(bind=_ENGINE)


def _override_get_db():
    db = _SessionFactory()
    try:
        yield db
    finally:
        db.close()


_ADMIN = User(id=1, username="admin_oa", hashed_password="", role="admin")
_REGULAR_USER = User(id=2, username="user_oa", hashed_password="", role="user")

_mini_app = FastAPI()
_mini_app.include_router(over_allocation_router)
_mini_app.dependency_overrides[get_db] = _override_get_db
_mini_app.dependency_overrides[get_current_user] = lambda: _ADMIN


@pytest.fixture(autouse=True)
def _clean():
    """Wipe all rows before each test."""
    db = _SessionFactory()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def db():
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(_mini_app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cycle(db, name="Jan/2026", start=date(2026, 1, 1), end=date(2026, 1, 31),
                is_active=True):
    cy = Cycle(name=name, start_date=start, end_date=end, is_active=is_active, is_closed=False)
    db.add(cy)
    db.flush()
    return cy


def _make_collab(db, name="Alice"):
    co = Collaborator(name=name)
    db.add(co)
    db.flush()
    return co


def _make_record(db, collab, cycle, pep, record_date, normal=8.0, extra=0.0, standby=0.0):
    r = TimesheetRecord(
        collaborator_id=collab.id,
        cycle_id=cycle.id,
        record_date=record_date,
        pep_wbs=pep,
        pep_description=f"Desc {pep}",
        normal_hours=normal,
        extra_hours=extra,
        standby_hours=standby,
        cost_per_hour=50.0,
        normal_cost=normal * 50.0,
        extra_cost=extra * 50.0 * 1.5,
        standby_cost=standby * 50.0 * 0.33,
    )
    db.add(r)
    db.flush()
    return r


@contextmanager
def _acting_as(user):
    """Temporarily override get_current_user on _mini_app."""
    saved = dict(_mini_app.dependency_overrides)
    _mini_app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(_mini_app, raise_server_exceptions=True) as c:
        yield c
    _mini_app.dependency_overrides.clear()
    _mini_app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOverAllocationEmpty:
    def test_no_data_returns_empty_list(self, client, db):
        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        assert r.json() == []


class TestOverAllocationBelowThreshold:
    def test_hours_at_or_below_threshold_excluded(self, client, db):
        """Single collaborator, single PEP, hours <= threshold → empty list."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Bob")
        # Default threshold is 24.0 from GlobalConfig (not set → uses 24.0 hard default)
        _make_record(db, co, cy, "PEP-001", date(2026, 1, 5), normal=8.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        assert r.json() == []

    def test_exactly_at_threshold_excluded(self, client, db):
        """Exactly 24h → not over threshold (strictly >), so excluded."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Carl")
        _make_record(db, co, cy, "PEP-002", date(2026, 1, 6), normal=24.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        assert r.json() == []


class TestOverAllocationViolation:
    def test_single_collaborator_single_pep_over_threshold(self, client, db):
        """Single collaborator, single PEP, hours > 24h → one violation."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Diana")
        _make_record(db, co, cy, "PEP-100", date(2026, 1, 10), normal=25.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        item = items[0]
        assert item["collaborator"] == "Diana"
        assert item["date"] == "2026-01-10"
        assert item["total_hours"] == pytest.approx(25.0)
        assert item["threshold"] == pytest.approx(24.0)
        assert item["pep_list"] == ["PEP-100"]

    def test_combined_hours_from_two_peps_same_day(self, client, db):
        """Single collaborator, two PEPs, same day, combined > threshold → one violation."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Eve")
        _make_record(db, co, cy, "PEP-A", date(2026, 1, 15), normal=13.0)
        _make_record(db, co, cy, "PEP-B", date(2026, 1, 15), normal=13.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        item = items[0]
        assert item["collaborator"] == "Eve"
        assert item["total_hours"] == pytest.approx(26.0)
        assert sorted(item["pep_list"]) == ["PEP-A", "PEP-B"]

    def test_includes_extra_and_standby_hours(self, client, db):
        """Total = normal + extra + standby, all counted towards threshold."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Frank")
        # normal=8, extra=8, standby=9 → total=25
        _make_record(db, co, cy, "PEP-X", date(2026, 1, 20), normal=8.0, extra=8.0, standby=9.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["total_hours"] == pytest.approx(25.0)


class TestOverAllocationCustomThreshold:
    def test_custom_threshold_param_overrides_default(self, client, db):
        """?threshold=10 → violations at 11h that default 24h would miss."""
        cy = _make_cycle(db)
        co = _make_collab(db, "Grace")
        _make_record(db, co, cy, "PEP-Y", date(2026, 1, 7), normal=11.0)
        db.commit()

        # Default threshold (24) → no violation
        r_default = client.get("/api/v2/over-allocation")
        assert r_default.json() == []

        # Custom threshold 10 → violation
        r_custom = client.get("/api/v2/over-allocation?threshold=10")
        assert r_custom.status_code == 200
        items = r_custom.json()
        assert len(items) == 1
        assert items[0]["collaborator"] == "Grace"
        assert items[0]["threshold"] == pytest.approx(10.0)

    def test_globalconfig_threshold_used_when_no_param(self, client, db):
        """When GlobalConfig.anomaly_max_daily_hours=10, a 11h day is a violation."""
        cfg = GlobalConfig(
            id=1,
            extra_hours_multiplier=1.5,
            standby_hours_multiplier=0.33,
            budget_warning_threshold=0.9,
            budget_critical_threshold=1.0,
            anomaly_max_daily_hours=10.0,
            timezone="America/Sao_Paulo",
        )
        db.add(cfg)
        cy = _make_cycle(db)
        co = _make_collab(db, "Hank")
        _make_record(db, co, cy, "PEP-Z", date(2026, 1, 8), normal=11.0)
        db.commit()

        r = client.get("/api/v2/over-allocation")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["threshold"] == pytest.approx(10.0)

    def test_explicit_threshold_param_overrides_globalconfig(self, client, db):
        """Explicit threshold=15 wins over GlobalConfig.anomaly_max_daily_hours=10."""
        cfg = GlobalConfig(
            id=1,
            extra_hours_multiplier=1.5,
            standby_hours_multiplier=0.33,
            budget_warning_threshold=0.9,
            budget_critical_threshold=1.0,
            anomaly_max_daily_hours=10.0,
            timezone="America/Sao_Paulo",
        )
        db.add(cfg)
        cy = _make_cycle(db)
        co = _make_collab(db, "Iris")
        _make_record(db, co, cy, "PEP-W", date(2026, 1, 9), normal=12.0)
        db.commit()

        # threshold=15 → 12h is NOT a violation
        r = client.get("/api/v2/over-allocation?threshold=15")
        assert r.json() == []

        # threshold=10 (same as config) → 12h IS a violation
        r2 = client.get("/api/v2/over-allocation?threshold=10")
        assert len(r2.json()) == 1


class TestOverAllocationDateFilter:
    def test_date_from_excludes_earlier_records(self, client, db):
        """Records before date_from are excluded."""
        cy = _make_cycle(db, "Jan/2026", date(2026, 1, 1), date(2026, 1, 31))
        co = _make_collab(db, "Jack")
        _make_record(db, co, cy, "PEP-001", date(2026, 1, 5), normal=25.0)  # before filter
        _make_record(db, co, cy, "PEP-001", date(2026, 1, 20), normal=25.0)  # within filter
        db.commit()

        r = client.get("/api/v2/over-allocation?date_from=2026-01-10")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["date"] == "2026-01-20"

    def test_date_to_excludes_later_records(self, client, db):
        """Records after date_to are excluded."""
        cy = _make_cycle(db, "Jan/2026", date(2026, 1, 1), date(2026, 1, 31))
        co = _make_collab(db, "Kate")
        _make_record(db, co, cy, "PEP-002", date(2026, 1, 5), normal=25.0)   # within filter
        _make_record(db, co, cy, "PEP-002", date(2026, 1, 25), normal=25.0)  # after filter
        db.commit()

        r = client.get("/api/v2/over-allocation?date_to=2026-01-15")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["date"] == "2026-01-05"

    def test_date_range_both_bounds(self, client, db):
        """date_from and date_to together form a window."""
        cy = _make_cycle(db, "Jan/2026", date(2026, 1, 1), date(2026, 1, 31))
        co = _make_collab(db, "Leo")
        _make_record(db, co, cy, "PEP-003", date(2026, 1, 3), normal=25.0)   # outside (before)
        _make_record(db, co, cy, "PEP-003", date(2026, 1, 10), normal=25.0)  # inside
        _make_record(db, co, cy, "PEP-003", date(2026, 1, 28), normal=25.0)  # outside (after)
        db.commit()

        r = client.get("/api/v2/over-allocation?date_from=2026-01-07&date_to=2026-01-20")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["date"] == "2026-01-10"


class TestOverAllocationAuth:
    def test_no_token_returns_401(self):
        """Without auth, the endpoint returns 401."""
        from backend.app.database import get_db as real_get_db

        # Build a truly unauthenticated app (no dependency overrides)
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                               poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine)

        def _db():
            db = session_factory()
            try:
                yield db
            finally:
                db.close()

        naked_app = FastAPI()
        naked_app.include_router(over_allocation_router)
        naked_app.dependency_overrides[get_db] = _db
        # Intentionally do NOT override get_current_user

        with TestClient(naked_app, raise_server_exceptions=True) as c:
            r = c.get("/api/v2/over-allocation")
        assert r.status_code == 401
