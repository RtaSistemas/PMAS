"""Audit cycle 3 (leftovers): inactive cycles in runway/concentration, ceil float noise."""
from __future__ import annotations

import calendar
from datetime import date

from backend.app.models import Collaborator, Cycle, Project, TimesheetRecord


def _cycle(db, name, y, m, active=True):
    last = calendar.monthrange(y, m)[1]
    c = Cycle(name=name, start_date=date(y, m, 1), end_date=date(y, m, last), is_active=active)
    db.add(c); db.commit(); db.refresh(c)
    return c


def _rec(db, cycle, collab, pep, hours):
    db.add(TimesheetRecord(
        collaborator_id=collab.id, cycle_id=cycle.id, record_date=cycle.start_date,
        pep_wbs=pep, pep_description="D", normal_hours=hours, extra_hours=0.0,
        standby_hours=0.0, cost_per_hour=10.0, normal_cost=hours * 10.0,
        extra_cost=0.0, standby_cost=0.0,
    ))
    db.commit()


def _setup(db, budget=100.0):
    col = Collaborator(name="Ana"); db.add(col)
    db.add(Project(pep_wbs="P-1", name="P1", budget_hours=budget, budget_cost=budget * 10, status="em_andamento"))
    db.commit(); db.refresh(col)
    return col


def test_runway_excludes_inactive_cycles(client, db_session, clean_db):
    col = _setup(db_session)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    cq = _cycle(db_session, "QUAR/2025", 2025, 2, active=False)
    _rec(db_session, c1, col, "P-1", 10.0)
    _rec(db_session, cq, col, "P-1", 50.0)
    row = client.get("/api/v2/runway").json()[0]
    assert row["consumed_hours"] == 10.0


def test_concentration_excludes_inactive_cycles(client, db_session, clean_db):
    col = _setup(db_session)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    cq = _cycle(db_session, "QUAR/2025", 2025, 2, active=False)
    _rec(db_session, c1, col, "P-1", 10.0)
    _rec(db_session, cq, col, "P-1", 50.0)
    rows = client.get("/api/v2/concentration").json()
    assert sum(r["total_hours"] for r in rows) == 10.0


def test_simulate_ceil_ignores_float_noise(client, db_session, clean_db):
    col = _setup(db_session, budget=21.7)
    c1 = _cycle(db_session, "JAN/2025", 2025, 1)
    _rec(db_session, c1, col, "P-1", 0.7)
    pid = db_session.query(Project).first().id
    body = client.post(f"/api/v2/projects/{pid}/simulate", json={}).json()
    assert body["cycles_to_complete"] == 30


def test_runway_ceil_ignores_float_noise(client, db_session, clean_db):
    col = _setup(db_session, budget=21.7)
    cycles = [_cycle(db_session, f"C{i:02d}", 2025 + i // 12, i % 12 + 1) for i in range(33)]
    _rec(db_session, cycles[0], col, "P-1", 0.7)
    row = client.get("/api/v2/runway").json()[0]
    assert row["estimated_completion_cycle"] == "C30"


def test_list_routes_accept_both_slash_forms(client, clean_db):
    for url in ("/api/my/notifications", "/api/my/notifications/",
                "/api/project-alerts", "/api/project-alerts/"):
        r = client.get(url, follow_redirects=False)
        assert r.status_code == 200, (url, r.status_code)


def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json() == {"status": "ready"}


def test_ready_returns_503_when_the_database_fails(client):
    from backend.app.database import get_db
    from backend.app.main import app

    class _Broken:
        def execute(self, *a, **k):
            raise RuntimeError("down")

    def _broken():
        yield _Broken()

    previous = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = _broken
    try:
        assert client.get("/ready").status_code == 503
    finally:
        app.dependency_overrides[get_db] = previous


def test_alias_routes_hidden_from_schema(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/my/notifications" not in paths
    assert "/api/project-alerts" not in paths
    assert "/api/my/notifications/" in paths


# ---------------------------------------------------------------------------
# Startup errors (run in a child process: the settings are read at import)
# ---------------------------------------------------------------------------

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _child(code, env):
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, **env}, timeout=60,
    )


def test_unwritable_log_file_falls_back_to_console(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("x")          # a file where a folder is needed
    r = _child("import backend.app.main as m; print('IMPORTED')", {
        "PMAS_LOG_FILE": str(blocker / "pmas.log"),
        "PMAS_DB_PATH": str(tmp_path / "t.db"),
    })
    assert "IMPORTED" in r.stdout, r.stderr[-400:]
    assert "Traceback" not in r.stderr


def test_log_file_folder_is_created(tmp_path):
    log_file = tmp_path / "new" / "dir" / "pmas.log"
    r = _child("import backend.app.main as m; print('IMPORTED')", {
        "PMAS_LOG_FILE": str(log_file), "PMAS_DB_PATH": str(tmp_path / "t.db"),
    })
    assert "IMPORTED" in r.stdout, r.stderr[-400:]
    assert log_file.parent.is_dir()


def test_unusable_db_path_gives_a_clear_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    r = _child("from backend.app.database import init_db; init_db()",
               {"PMAS_DB_PATH": str(blocker / "pmas.db")})
    assert r.returncode != 0
    assert "PMAS_DB_PATH" in r.stderr
    assert "Traceback" not in r.stderr


def test_missing_db_folder_is_created(tmp_path):
    db = tmp_path / "a" / "b" / "pmas.db"
    r = _child("from backend.app.database import init_db; init_db(); print('OK')",
               {"PMAS_DB_PATH": str(db)})
    assert "OK" in r.stdout, r.stderr[-400:]
    assert db.exists()
