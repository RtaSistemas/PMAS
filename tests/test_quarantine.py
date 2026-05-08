from __future__ import annotations

import pytest

from backend.app.models import QuarantineRecord, UploadSession


def _add_session(db):
    s = UploadSession(
        uploaded_by_username="test",
        source_file="t.csv",
        records_inserted=0, records_skipped=0, quarantine_added=1,
        warning_count=0, info_count=0, status="ok",
    )
    db.add(s)
    db.flush()
    return s


def _add_qr(db, session_id=None, reason="test reason", reviewed=False):
    qr = QuarantineRecord(
        upload_session_id=session_id,
        uploaded_by_username="test",
        raw_data={"col": "val"},
        quarantine_reason=reason,
        reviewed=reviewed,
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr


class TestQuarantineList:
    def test_empty_list(self, client):
        r = client.get("/api/quarantine")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_quarantine_records(self, client, db_session):
        _add_qr(db_session)
        r = client.get("/api/quarantine")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_filter_pending(self, client, db_session):
        _add_qr(db_session, reason="pending", reviewed=False)
        _add_qr(db_session, reason="reviewed", reviewed=True)
        r = client.get("/api/quarantine?reviewed=false")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["quarantine_reason"] == "pending"

    def test_filter_reviewed(self, client, db_session):
        _add_qr(db_session, reason="pending", reviewed=False)
        _add_qr(db_session, reason="reviewed", reviewed=True)
        r = client.get("/api/quarantine?reviewed=true")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["reviewed"] is True

    def test_filter_by_session(self, client, db_session):
        s = _add_session(db_session)
        _add_qr(db_session, session_id=s.id)
        _add_qr(db_session)  # no session
        r = client.get(f"/api/quarantine?upload_session_id={s.id}")
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestQuarantineReview:
    def test_mark_as_reviewed(self, client, db_session):
        qr = _add_qr(db_session)
        r = client.patch(f"/api/quarantine/{qr.id}/review", json={"reviewed": True})
        assert r.status_code == 200
        data = r.json()
        assert data["reviewed"] is True
        assert data["reviewed_by"] is not None
        assert data["reviewed_at"] is not None

    def test_reopen_reviewed(self, client, db_session):
        qr = _add_qr(db_session, reviewed=True)
        r = client.patch(f"/api/quarantine/{qr.id}/review", json={"reviewed": False})
        assert r.status_code == 200
        assert r.json()["reviewed"] is False
        assert r.json()["reviewed_at"] is None

    def test_not_found(self, client):
        r = client.patch("/api/quarantine/99999/review", json={"reviewed": True})
        assert r.status_code == 404
