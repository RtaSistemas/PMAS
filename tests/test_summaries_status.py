"""
Tests for GET /api/summaries/status — staleness detection endpoint.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.models import (
    CollaboratorCycleSummary,
    Collaborator,
    Cycle,
    PepCycleSummary,
    UploadSession,
    User,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_URL = "/api/summaries/status"


def _ts(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str).replace(tzinfo=None)


def _make_upload(db, at: datetime) -> UploadSession:
    s = UploadSession(
        uploaded_at=at,
        uploaded_by_username="admin",
        source_file="test.csv",
        records_inserted=1,
        records_skipped=0,
        quarantine_added=0,
        warning_count=0,
        info_count=0,
        status="ok",
    )
    db.add(s)
    db.flush()
    return s


def _make_pep_summary(db, pep: str, cycle_id: int, refreshed_at: datetime) -> PepCycleSummary:
    s = PepCycleSummary(
        pep_wbs=pep,
        cycle_id=cycle_id,
        refreshed_at=refreshed_at,
    )
    db.add(s)
    db.flush()
    return s


def _make_collab_summary(db, collab_id: int, cycle_id: int, refreshed_at: datetime) -> CollaboratorCycleSummary:
    s = CollaboratorCycleSummary(
        collaborator_id=collab_id,
        cycle_id=cycle_id,
        refreshed_at=refreshed_at,
    )
    db.add(s)
    db.flush()
    return s


# ── tests ─────────────────────────────────────────────────────────────────────

class TestSummariesStatus:
    def test_no_uploads_returns_not_stale(self, client):
        """If there are no uploads yet, summaries are not considered stale."""
        r = client.get(_URL)
        assert r.status_code == 200
        assert r.json()["stale"] is False

    def test_summaries_fresh_when_rebuilt_after_upload(self, client, db_session):
        """Summaries rebuilt after the latest upload → not stale."""
        upload_at = _ts("2026-01-15T10:00:00")
        refresh_at = _ts("2026-01-15T10:00:30")  # 30s later

        cycle = Cycle(name="Jan/2026", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        db_session.add(cycle)
        db_session.flush()

        collab = Collaborator(name="Alice")
        db_session.add(collab)
        db_session.flush()

        _make_upload(db_session, upload_at)
        _make_pep_summary(db_session, "60IT-001", cycle.id, refresh_at)
        _make_collab_summary(db_session, collab.id, cycle.id, refresh_at)
        db_session.commit()

        r = client.get(_URL)
        assert r.status_code == 200
        assert r.json()["stale"] is False

    def test_stale_when_summary_older_than_upload(self, client, db_session):
        """Summary refreshed BEFORE the latest upload → stale."""
        refresh_at = _ts("2026-01-15T09:00:00")
        upload_at = _ts("2026-01-15T10:00:00")   # upload is NEWER

        cycle = Cycle(name="Jan/2026", start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        db_session.add(cycle)
        db_session.flush()

        collab = Collaborator(name="Bob")
        db_session.add(collab)
        db_session.flush()

        _make_upload(db_session, upload_at)
        _make_pep_summary(db_session, "60IT-001", cycle.id, refresh_at)
        _make_collab_summary(db_session, collab.id, cycle.id, refresh_at)
        db_session.commit()

        r = client.get(_URL)
        assert r.status_code == 200
        data = r.json()
        assert data["stale"] is True
        assert data["reason"] is not None

    def test_stale_when_no_summaries_but_uploads_exist(self, client, db_session):
        """Uploads exist but no summaries were ever built → stale."""
        _make_upload(db_session, _ts("2026-01-15T10:00:00"))
        db_session.commit()

        r = client.get(_URL)
        assert r.status_code == 200
        assert r.json()["stale"] is True

    def test_response_includes_timestamps(self, client, db_session):
        """Response must include latest_upload_at and oldest refresh timestamps."""
        upload_at = _ts("2026-02-01T08:00:00")
        _make_upload(db_session, upload_at)
        db_session.commit()

        r = client.get(_URL)
        assert r.status_code == 200
        data = r.json()
        assert "latest_upload_at" in data
        assert data["latest_upload_at"] is not None

    def test_requires_admin(self, client, db_session):
        """Non-admin users must receive 403."""
        from backend.app.deps import get_current_user
        from backend.app.main import app

        non_admin = User(id=999, username="user1", hashed_password="", role="user", must_change_password=False)
        override = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: non_admin
        try:
            r = client.get(_URL)
            assert r.status_code == 403
        finally:
            if override:
                app.dependency_overrides[get_current_user] = override
            else:
                del app.dependency_overrides[get_current_user]
