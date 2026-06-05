from __future__ import annotations

import io
from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.database import get_db
from backend.app.deps import get_current_user
from backend.app.main import app
from backend.app.models import Cycle, Notification, User
from backend.app.services.notifications_svc import create_notification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_csv(collaborator="Ana Lima", record_date="15/01/2026", hours=8.0) -> bytes:
    df = pd.DataFrame([{
        "Colaborador": collaborator,
        "Data": record_date,
        "Horas totais (decimal)": hours,
        "Hora extra": "Não",
        "Hora sobreaviso": "Não",
        "Código PEP": "60OP-001",
        "PEP": "Projeto Alpha",
    }])
    return df.to_csv(index=False).encode("utf-8")


def _seed_cycle(db) -> Cycle:
    cycle = Cycle(
        name="Jan/2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


# ---------------------------------------------------------------------------
# Second mock user (user id 8888) — distinct from conftest's mock admin (9999)
# ---------------------------------------------------------------------------
_MOCK_USER2 = User(id=8888, username="other_user", hashed_password="", role="user")


@pytest.fixture
def client_user2():
    """Independent client authenticated as a second user (non-admin)."""
    from tests.conftest import _override_get_db, _MOCK_ADMIN  # type: ignore[attr-defined]
    # Temporarily override get_current_user to _MOCK_USER2
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: _MOCK_USER2
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    # Restore admin override (as conftest session-scoped client expects)
    app.dependency_overrides[get_current_user] = lambda: _MOCK_ADMIN


# ===========================================================================
# Tests
# ===========================================================================


class TestCreateNotificationViaUpload:
    """Upload triggers a notification for the uploader (user id 9999 = mock admin)."""

    def test_upload_creates_notification(self, client, db_session):
        _seed_cycle(db_session)
        resp = client.post(
            "/api/upload-timesheet",
            files={"file": ("jan.csv", io.BytesIO(_make_csv()), "text/csv")},
        )
        assert resp.status_code == 200
        # Expire session cache so we see rows committed by the HTTP request's session
        db_session.expire_all()
        notifs = db_session.query(Notification).filter_by(user_id=9999).all()
        assert len(notifs) == 1
        assert "jan.csv" in notifs[0].message
        assert "registros aceitos" in notifs[0].message

    def test_upload_notification_level_info_when_no_quarantine(self, client, db_session):
        _seed_cycle(db_session)
        client.post(
            "/api/upload-timesheet",
            files={"file": ("ok.csv", io.BytesIO(_make_csv()), "text/csv")},
        )
        db_session.expire_all()
        notif = db_session.query(Notification).filter_by(user_id=9999).first()
        assert notif is not None
        assert notif.level == "info"

    def test_upload_notification_level_warning_when_quarantine(self, client, db_session):
        """Row with no matching cycle goes to quarantine → notification level = warning."""
        # No cycle seeded — date 2020 has no matching cycle → quarantine
        resp = client.post(
            "/api/upload-timesheet",
            files={"file": ("warn.csv", io.BytesIO(_make_csv(record_date="15/01/2020")), "text/csv")},
        )
        assert resp.status_code == 200
        db_session.expire_all()
        notif = db_session.query(Notification).filter_by(user_id=9999).first()
        assert notif is not None
        assert notif.level == "warning"


class TestGetNotifications:
    """GET /api/my/notifications/ returns the current user's notifications."""

    def test_get_returns_empty_list(self, client):
        resp = client.get("/api/my/notifications/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_returns_notifications(self, client, db_session):
        create_notification(db_session, 9999, "Hello world", level="info")
        db_session.commit()
        resp = client.get("/api/my/notifications/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["message"] == "Hello world"

    def test_unread_count_correct(self, client, db_session):
        create_notification(db_session, 9999, "A", level="info")
        create_notification(db_session, 9999, "B", level="warning")
        db_session.commit()
        resp = client.get("/api/my/notifications/")
        data = resp.json()
        unread = [n for n in data if not n["is_read"]]
        assert len(unread) == 2

    def test_level_is_preserved(self, client, db_session):
        create_notification(db_session, 9999, "error msg", level="error")
        db_session.commit()
        resp = client.get("/api/my/notifications/")
        assert resp.json()[0]["level"] == "error"


class TestMarkRead:
    """POST /{id}/read marks a single notification as read."""

    def test_mark_single_read(self, client, db_session):
        notif = create_notification(db_session, 9999, "Mark me", level="info")
        db_session.commit()
        db_session.refresh(notif)
        resp = client.post(f"/api/my/notifications/{notif.id}/read")
        assert resp.status_code == 200
        assert resp.json()["is_read"] is True

    def test_mark_read_not_found(self, client):
        resp = client.post("/api/my/notifications/99999/read")
        assert resp.status_code == 404


class TestMarkAllRead:
    """POST /read-all marks all as read for the current user."""

    def test_mark_all_read(self, client, db_session):
        create_notification(db_session, 9999, "A", level="info")
        create_notification(db_session, 9999, "B", level="info")
        db_session.commit()
        resp = client.post("/api/my/notifications/read-all")
        assert resp.status_code == 200
        unread_count = (
            db_session.query(Notification)
            .filter_by(user_id=9999, is_read=False)
            .count()
        )
        assert unread_count == 0


class TestDeleteNotification:
    """DELETE /{id} removes the notification."""

    def test_delete_removes_notification(self, client, db_session):
        notif = create_notification(db_session, 9999, "Delete me", level="info")
        db_session.commit()
        db_session.refresh(notif)
        notif_id = notif.id
        resp = client.delete(f"/api/my/notifications/{notif_id}")
        assert resp.status_code == 204
        # Expire session cache so we get a fresh query result
        db_session.expire_all()
        assert db_session.get(Notification, notif_id) is None

    def test_delete_not_found(self, client):
        resp = client.delete("/api/my/notifications/99999")
        assert resp.status_code == 404


class TestUserIsolation:
    """Users cannot see or act on each other's notifications."""

    def test_admin_does_not_see_other_users_notifications(self, client, db_session):
        """Admin only sees their own notifications, not those seeded for user2."""
        create_notification(db_session, 9999, "Admin notif", level="info")
        create_notification(db_session, _MOCK_USER2.id, "User2 notif", level="info")
        db_session.commit()

        admin_data = client.get("/api/my/notifications/").json()
        # Admin should see only their own notification
        assert len(admin_data) == 1
        assert admin_data[0]["message"] == "Admin notif"

    def test_user2_does_not_see_admin_notifications(self, client_user2, db_session):
        """User2 only sees their own notifications."""
        create_notification(db_session, 9999, "Admin notif", level="info")
        create_notification(db_session, _MOCK_USER2.id, "User2 notif", level="info")
        db_session.commit()

        user2_data = client_user2.get("/api/my/notifications/").json()
        assert len(user2_data) == 1
        assert user2_data[0]["message"] == "User2 notif"

    def test_cannot_delete_other_users_notification(self, client, db_session):
        notif = create_notification(db_session, _MOCK_USER2.id, "User2 only", level="info")
        db_session.commit()
        db_session.refresh(notif)
        # Admin (9999) tries to delete user2's notification → 404
        resp = client.delete(f"/api/my/notifications/{notif.id}")
        assert resp.status_code == 404
