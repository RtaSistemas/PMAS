"""A restricted user must not see other PEPs in the project list or in the team list."""
from __future__ import annotations

from tests.test_audit_analytics import (
    _as, _collab, _cycle, _project, _rec, _restricted_user,
)


def test_restricted_user_sees_only_allowed_projects_and_team(client, db_session):
    cyc = _cycle(db_session, "JAN", 2025, 1)
    ok, secret = _project(db_session, "OK-001", 100, 1000), _project(db_session, "SEC-999", 100, 1000)
    ana, spy = _collab(db_session, "Ana"), _collab(db_session, "Segredo")
    _rec(db_session, cyc, ana, "OK-001", 8)
    _rec(db_session, cyc, spy, "SEC-999", 8)
    user = _restricted_user(db_session, ok)
    with _as(user) as c:
        assert [p["pep_wbs"] for p in c.get("/api/projects").json()] == ["OK-001"]
        assert [m["name"] for m in c.get("/api/team").json()] == ["Ana"]
    assert len(client.get("/api/projects").json()) == 2
    assert len(client.get("/api/team").json()) == 2


def test_bulk_seniority_assign_returns_the_team(client, db_session):
    from backend.app.models import SeniorityLevel
    _collab(db_session, "Ana")
    level = SeniorityLevel(name="Pleno")
    db_session.add(level)
    db_session.commit()
    r = client.put("/api/team/bulk-seniority", json={"seniority_level_id": level.id})
    assert r.status_code == 200, r.text
    assert r.json()[0]["seniority_level_name"] == "Pleno"
