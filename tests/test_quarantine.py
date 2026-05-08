from __future__ import annotations

from datetime import date

import pytest

from backend.app.models import Collaborator, Cycle, QuarantineRecord, TimesheetRecord, UploadSession


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


def _add_qr(db, session_id=None, reason="test reason", reviewed=False, raw_data=None):
    qr = QuarantineRecord(
        upload_session_id=session_id,
        uploaded_by_username="test",
        raw_data=raw_data or {"col": "val"},
        quarantine_reason=reason,
        reviewed=reviewed,
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr


def _raw_data_for_approve(cycle: Cycle) -> dict:
    """Build a raw_data dict matching CSV column names for a valid approve payload."""
    return {
        "Colaborador": "João Aprovado",
        "Data": str(cycle.start_date),
        "Horas totais (decimal)": "8.0",
        "Hora extra": "Não",
        "Hora sobreaviso": "Não",
        "Código PEP": "60OP-TEST",
        "PEP": "Projeto Aprovado",
    }


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

    def test_review_status_default_pending(self, client, db_session):
        _add_qr(db_session)
        data = client.get("/api/quarantine").json()
        assert data[0]["review_status"] == "pending"

    def test_rule_description_null_when_no_rule(self, client, db_session):
        _add_qr(db_session)
        data = client.get("/api/quarantine").json()
        assert data[0]["rule_description"] is None

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

    def test_filter_by_review_status(self, client, db_session):
        qr = _add_qr(db_session)
        client.post(f"/api/quarantine/{qr.id}/reject")
        r = client.get("/api/quarantine?review_status=rejected")
        assert r.status_code == 200
        assert len(r.json()) == 1


class TestQuarantineGet:
    def test_get_single_record(self, client, db_session):
        qr = _add_qr(db_session, reason="detalhe")
        r = client.get(f"/api/quarantine/{qr.id}")
        assert r.status_code == 200
        assert r.json()["quarantine_reason"] == "detalhe"

    def test_get_not_found(self, client):
        r = client.get("/api/quarantine/99999")
        assert r.status_code == 404


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


class TestQuarantineReject:
    def test_reject_sets_status(self, client, db_session):
        qr = _add_qr(db_session)
        r = client.post(f"/api/quarantine/{qr.id}/reject")
        assert r.status_code == 200
        data = r.json()
        assert data["review_status"] == "rejected"
        assert data["reviewed"] is True
        assert data["reviewed_by"] is not None

    def test_reject_not_found(self, client):
        r = client.post("/api/quarantine/99999/reject")
        assert r.status_code == 404

    def test_cannot_reject_approved(self, client, db_session, sample_cycle):
        raw = _raw_data_for_approve(sample_cycle)
        qr = _add_qr(db_session, raw_data=raw)
        client.post(f"/api/quarantine/{qr.id}/approve")
        r = client.post(f"/api/quarantine/{qr.id}/reject")
        assert r.status_code == 409


class TestQuarantineApprove:
    def test_approve_creates_timesheet_record(self, client, db_session, sample_cycle):
        raw = _raw_data_for_approve(sample_cycle)
        qr = _add_qr(db_session, raw_data=raw)

        r = client.post(f"/api/quarantine/{qr.id}/approve")
        assert r.status_code == 200
        data = r.json()
        assert data["review_status"] == "approved"
        assert data["reviewed"] is True

        records = db_session.query(TimesheetRecord).all()
        assert len(records) == 1
        assert records[0].normal_hours == 8.0

    def test_approve_creates_collaborator_if_new(self, client, db_session, sample_cycle):
        raw = _raw_data_for_approve(sample_cycle)
        qr = _add_qr(db_session, raw_data=raw)
        client.post(f"/api/quarantine/{qr.id}/approve")

        collab = db_session.query(Collaborator).filter_by(name="João Aprovado").first()
        assert collab is not None

    def test_approve_overtime_flag(self, client, db_session, sample_cycle):
        raw = _raw_data_for_approve(sample_cycle)
        raw["Hora extra"] = "Sim"
        qr = _add_qr(db_session, raw_data=raw)
        client.post(f"/api/quarantine/{qr.id}/approve")

        rec = db_session.query(TimesheetRecord).first()
        assert rec.extra_hours == 8.0
        assert rec.normal_hours == 0.0

    def test_approve_idempotent_conflict(self, client, db_session, sample_cycle):
        raw = _raw_data_for_approve(sample_cycle)
        qr = _add_qr(db_session, raw_data=raw)
        client.post(f"/api/quarantine/{qr.id}/approve")
        r = client.post(f"/api/quarantine/{qr.id}/approve")
        assert r.status_code == 409

    def test_approve_missing_collaborator_field(self, client, db_session):
        qr = _add_qr(db_session, raw_data={"Data": "2026-01-15", "Horas totais (decimal)": "8"})
        r = client.post(f"/api/quarantine/{qr.id}/approve")
        assert r.status_code == 422

    def test_approve_no_active_cycle(self, client, db_session):
        raw = {
            "Colaborador": "Maria",
            "Data": "1990-01-01",
            "Horas totais (decimal)": "8",
        }
        qr = _add_qr(db_session, raw_data=raw)
        r = client.post(f"/api/quarantine/{qr.id}/approve")
        assert r.status_code == 422
        assert "ciclo" in r.json()["detail"].lower()

    def test_approve_not_found(self, client):
        r = client.post("/api/quarantine/99999/approve")
        assert r.status_code == 404
