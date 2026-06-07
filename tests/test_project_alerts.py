from __future__ import annotations

from datetime import date

import pytest

from backend.app.models import GlobalConfig, Project, ProjectAlert, User, UserProjectAccess
from backend.app.services.notifications_svc import (
    _resolve_project_alerts,
    _upsert_project_alert,
    notify_threshold_crossings,
    notify_schedule_risk,
)
from backend.app.utils import now_br


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(db, pep_wbs="60IT-TEST-01", budget_hours=100.0):
    p = Project(pep_wbs=pep_wbs, name=f"Test {pep_wbs}", budget_hours=budget_hours, status="ativo")
    db.add(p)
    db.flush()
    return p


def _make_config(db):
    cfg = GlobalConfig(
        id=1, extra_hours_multiplier=1.5, standby_hours_multiplier=0.33,
        budget_warning_threshold=0.9, budget_critical_threshold=1.0,
        spi_warning_threshold=0.85, spi_risk_consecutive_cycles=2,
    )
    db.add(cfg)
    db.flush()
    return cfg


# ---------------------------------------------------------------------------
# _upsert_project_alert — deduplication logic
# ---------------------------------------------------------------------------

class TestUpsertProjectAlert:
    def test_creates_new_alert(self, db_session):
        p = _make_project(db_session)
        created = _upsert_project_alert(
            db_session, p.id, p.pep_wbs, "budget_warning", "warning", "Test msg"
        )
        db_session.flush()
        assert created is True
        alerts = db_session.query(ProjectAlert).filter_by(project_id=p.id).all()
        assert len(alerts) == 1
        assert alerts[0].is_resolved is False

    def test_same_level_no_duplicate(self, db_session):
        p = _make_project(db_session)
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "msg1")
        db_session.flush()
        created = _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "msg2")
        db_session.flush()
        assert created is False
        count = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=False).count()
        assert count == 1

    def test_level_change_resolves_old_and_creates_new(self, db_session):
        p = _make_project(db_session)
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "msg1")
        db_session.flush()
        created = _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "error", "msg2")
        db_session.flush()
        assert created is True
        resolved = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=True).all()
        active   = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=False).all()
        assert len(resolved) == 1
        assert len(active) == 1
        assert active[0].level == "error"

    def test_different_alert_types_coexist(self, db_session):
        p = _make_project(db_session)
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "budget msg")
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "schedule_risk",  "warning", "spi msg")
        db_session.flush()
        count = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=False).count()
        assert count == 2


# ---------------------------------------------------------------------------
# _resolve_project_alerts
# ---------------------------------------------------------------------------

class TestResolveProjectAlerts:
    def test_resolve_single_type(self, db_session):
        p = _make_project(db_session)
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "msg")
        db_session.flush()
        _resolve_project_alerts(db_session, p.id, "budget_warning")
        db_session.flush()
        alert = db_session.query(ProjectAlert).filter_by(project_id=p.id).first()
        assert alert.is_resolved is True
        assert alert.resolved_at is not None

    def test_resolve_does_not_affect_other_types(self, db_session):
        p = _make_project(db_session)
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "budget_warning", "warning", "b msg")
        _upsert_project_alert(db_session, p.id, p.pep_wbs, "schedule_risk",  "warning", "s msg")
        db_session.flush()
        _resolve_project_alerts(db_session, p.id, "budget_warning")
        db_session.flush()
        spi = db_session.query(ProjectAlert).filter_by(project_id=p.id, alert_type="schedule_risk").first()
        assert spi.is_resolved is False


# ---------------------------------------------------------------------------
# notify_threshold_crossings
# ---------------------------------------------------------------------------

class TestNotifyThresholdCrossings:
    def test_creates_alert_when_threshold_crossed(self, db_session):
        from backend.app.models import Cycle, PepCycleSummary
        _make_config(db_session)
        p = _make_project(db_session, "60IT-BUDGET-01", budget_hours=100.0)
        cycle = Cycle(name="C1", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
        db_session.add(cycle)
        db_session.flush()
        db_session.add(PepCycleSummary(
            pep_wbs=p.pep_wbs, cycle_id=cycle.id,
            total_hours=95.0, total_cost=0.0, refreshed_at=now_br(),
        ))
        db_session.flush()

        notify_threshold_crossings(db_session, [p.pep_wbs])
        db_session.flush()

        alert = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=False).first()
        assert alert is not None
        assert alert.alert_type == "budget_warning"
        assert alert.level == "warning"

    def test_auto_resolves_on_recovery(self, db_session):
        from backend.app.models import Cycle, PepCycleSummary
        _make_config(db_session)
        p = _make_project(db_session, "60IT-RECOVER-01", budget_hours=100.0)
        cycle = Cycle(name="C1", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
        db_session.add(cycle)
        db_session.flush()
        # Seed existing active alert
        db_session.add(ProjectAlert(
            project_id=p.id, pep_wbs=p.pep_wbs,
            alert_type="budget_warning", level="warning",
            message="old", created_at=now_br(),
        ))
        db_session.add(PepCycleSummary(
            pep_wbs=p.pep_wbs, cycle_id=cycle.id,
            total_hours=50.0, total_cost=0.0, refreshed_at=now_br(),
        ))
        db_session.flush()

        notify_threshold_crossings(db_session, [p.pep_wbs])
        db_session.flush()

        alert = db_session.query(ProjectAlert).filter_by(project_id=p.id).first()
        assert alert.is_resolved is True

    def test_overrun_creates_error_level(self, db_session):
        from backend.app.models import Cycle, PepCycleSummary
        _make_config(db_session)
        p = _make_project(db_session, "60IT-OVERRUN-01", budget_hours=100.0)
        cycle = Cycle(name="C1", start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
        db_session.add(cycle)
        db_session.flush()
        db_session.add(PepCycleSummary(
            pep_wbs=p.pep_wbs, cycle_id=cycle.id,
            total_hours=105.0, total_cost=0.0, refreshed_at=now_br(),
        ))
        db_session.flush()

        notify_threshold_crossings(db_session, [p.pep_wbs])
        db_session.flush()

        alert = db_session.query(ProjectAlert).filter_by(project_id=p.id, is_resolved=False).first()
        assert alert is not None
        assert alert.alert_type == "budget_overrun"
        assert alert.level == "error"

    def test_no_crash_on_empty_pep_list(self, db_session):
        notify_threshold_crossings(db_session, [])

    def test_no_crash_on_unknown_pep(self, db_session):
        _make_config(db_session)
        notify_threshold_crossings(db_session, ["NONEXISTENT-PEP"])


# ---------------------------------------------------------------------------
# Admin endpoint GET /api/project-alerts
# ---------------------------------------------------------------------------

class TestAdminProjectAlertsEndpoint:
    def test_list_empty(self, client):
        r = client.get("/api/project-alerts/")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_alert(self, client, db_session):
        p = _make_project(db_session)
        db_session.add(ProjectAlert(
            project_id=p.id, pep_wbs=p.pep_wbs,
            alert_type="budget_warning", level="warning",
            message="Test alert", created_at=now_br(),
        ))
        db_session.commit()
        r = client.get("/api/project-alerts/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["pep_wbs"] == p.pep_wbs
        assert data[0]["alert_type"] == "budget_warning"
        assert data[0]["is_resolved"] is False

    def test_filter_by_pep(self, client, db_session):
        p1 = _make_project(db_session, "60IT-P1-01")
        p2 = _make_project(db_session, "60IT-P2-01")
        db_session.add(ProjectAlert(project_id=p1.id, pep_wbs=p1.pep_wbs, alert_type="budget_warning", level="warning", message="m1", created_at=now_br()))
        db_session.add(ProjectAlert(project_id=p2.id, pep_wbs=p2.pep_wbs, alert_type="budget_warning", level="warning", message="m2", created_at=now_br()))
        db_session.commit()
        r = client.get(f"/api/project-alerts/?pep_wbs={p1.pep_wbs}")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["pep_wbs"] == p1.pep_wbs

    def test_filter_by_resolved(self, client, db_session):
        p = _make_project(db_session)
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="budget_warning", level="warning", message="active", created_at=now_br(), is_resolved=False))
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="schedule_risk",  level="warning", message="resolved", created_at=now_br(), is_resolved=True, resolved_at=now_br()))
        db_session.commit()
        r_active   = client.get("/api/project-alerts/?is_resolved=false")
        r_resolved = client.get("/api/project-alerts/?is_resolved=true")
        assert r_active.status_code == 200
        assert len(r_active.json()) == 1
        assert r_active.json()[0]["is_resolved"] is False
        assert r_resolved.status_code == 200
        assert len(r_resolved.json()) == 1
        assert r_resolved.json()[0]["is_resolved"] is True

    def test_filter_by_alert_type(self, client, db_session):
        p = _make_project(db_session)
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="budget_warning", level="warning", message="b", created_at=now_br()))
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="schedule_risk",  level="warning", message="s", created_at=now_br()))
        db_session.commit()
        r = client.get("/api/project-alerts/?alert_type=schedule_risk")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["alert_type"] == "schedule_risk"


# ---------------------------------------------------------------------------
# My alerts endpoint GET /api/my/alerts (ACL filtered)
# ---------------------------------------------------------------------------

class TestMyAlertsEndpoint:
    def test_admin_sees_all_alerts(self, client, db_session):
        p = _make_project(db_session, "60IT-MY-01")
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="budget_warning", level="warning", message="msg", created_at=now_br()))
        db_session.commit()
        r = client.get("/api/my/alerts")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_filter_by_resolved_on_my_alerts(self, client, db_session):
        p = _make_project(db_session, "60IT-MY-02")
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="budget_warning", level="warning", message="a", created_at=now_br(), is_resolved=False))
        db_session.add(ProjectAlert(project_id=p.id, pep_wbs=p.pep_wbs, alert_type="schedule_risk",  level="warning", message="b", created_at=now_br(), is_resolved=True, resolved_at=now_br()))
        db_session.commit()
        r = client.get("/api/my/alerts?is_resolved=false")
        assert r.status_code == 200
        data = r.json()
        assert all(not a["is_resolved"] for a in data)

    def test_user_acl_filters_alerts(self, db_session):
        from fastapi.testclient import TestClient
        from backend.app.deps import get_current_user
        from backend.app.main import app

        p_allowed  = _make_project(db_session, "60IT-ACL-ALLOW-01")
        p_denied   = _make_project(db_session, "60IT-ACL-DENY-01")
        regular_user = User(id=8888, username="regular_test", hashed_password="", role="user")
        db_session.add(regular_user)
        db_session.flush()
        db_session.add(UserProjectAccess(user_id=regular_user.id, project_id=p_allowed.id))
        db_session.add(ProjectAlert(project_id=p_allowed.id, pep_wbs=p_allowed.pep_wbs, alert_type="budget_warning", level="warning", message="allowed", created_at=now_br()))
        db_session.add(ProjectAlert(project_id=p_denied.id,  pep_wbs=p_denied.pep_wbs,  alert_type="budget_warning", level="warning", message="denied",  created_at=now_br()))
        db_session.commit()

        orig = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = lambda: regular_user
        try:
            with TestClient(app, raise_server_exceptions=True) as c:
                r = c.get("/api/my/alerts")
            assert r.status_code == 200
            peps = {a["pep_wbs"] for a in r.json()}
            assert p_allowed.pep_wbs in peps
            assert p_denied.pep_wbs not in peps
        finally:
            if orig is not None:
                app.dependency_overrides[get_current_user] = orig
            else:
                from backend.app.deps import get_current_user as gcu
                from tests.conftest import _MOCK_ADMIN  # type: ignore[import]
                app.dependency_overrides[get_current_user] = lambda: _MOCK_ADMIN
