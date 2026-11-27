"""Backup of the database before pending migrations (WO-001 T5).

init_db copies an existing, non-empty database with VACUUM INTO before it applies a migration.
Each case starts PMAS in a new process, because the engine is created with the database path.
"""
from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAST = "M013_timesheet_record_date_idx"
FIRST = "M001_tr_cost_per_hour"


def _start(db: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PMAS_")}
    env["PMAS_DB_PATH"] = str(db)
    env.update(extra_env or {})
    code = "from backend.app.database import init_db; init_db()"
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)


def _new_db() -> Path:
    return Path(tempfile.mkdtemp()) / "pmas.db"


def _backups(db: Path) -> list[Path]:
    return sorted(db.parent.glob(f"{db.name}.pre-*.bak"))


def _versions(db: Path) -> set[str]:
    con = sqlite3.connect(db)
    try:
        return {r[0] for r in con.execute("SELECT version FROM schema_migration")}
    finally:
        con.close()


@pytest.fixture()
def current_db() -> Path:
    """A database that PMAS created and migrated, with a row in a user table."""
    db = _new_db()
    assert _start(db).returncode == 0
    con = sqlite3.connect(db)
    con.execute("INSERT INTO seniority_level (name) VALUES ('Pleno')")
    con.execute("INSERT INTO collaborator (name) VALUES ('Ana')")
    con.commit()
    con.close()
    assert _backups(db) == []
    return db


def _rewind(db: Path, version: str) -> None:
    """Mark one migration as not applied, as on an install from before that migration."""
    con = sqlite3.connect(db)
    con.execute("DELETE FROM schema_migration WHERE version = ?", (version,))
    con.commit()
    con.close()


class TestBackupBeforePendingMigrations:
    def test_a_pending_migration_makes_a_backup_named_after_it(self, current_db):
        _rewind(current_db, LAST)
        r = _start(current_db)
        assert r.returncode == 0, r.stderr
        assert [b.name for b in _backups(current_db)] == [f"pmas.db.pre-{LAST}.bak"]
        assert LAST in _versions(current_db)                        # the migration did run

    def test_the_backup_opens_and_has_the_rows_from_before_the_migration(self, current_db):
        _rewind(current_db, LAST)
        _start(current_db)
        (backup,) = _backups(current_db)
        con = sqlite3.connect(backup)
        assert con.execute("SELECT name FROM seniority_level").fetchall() == [("Pleno",)]
        assert con.execute("SELECT name FROM collaborator").fetchall() == [("Ana",)]
        assert con.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert LAST not in {r[0] for r in con.execute("SELECT version FROM schema_migration")}   # the state before
        con.close()

    def test_the_name_uses_the_first_pending_migration(self, current_db):
        for v in ("M011_budget_revision_table", LAST):
            _rewind(current_db, v)
        _start(current_db)
        assert [b.name for b in _backups(current_db)] == ["pmas.db.pre-M011_budget_revision_table.bak"]

    def test_an_up_to_date_database_makes_no_backup(self, current_db):
        assert _start(current_db).returncode == 0
        assert _start(current_db).returncode == 0
        assert _backups(current_db) == []

    def test_a_new_database_makes_no_backup(self):
        db = _new_db()
        assert _start(db).returncode == 0
        assert _backups(db) == []
        assert _start(db).returncode == 0
        assert _backups(db) == []

    def test_an_empty_database_file_makes_no_backup(self):
        db = _new_db()
        db.touch()
        assert _start(db).returncode == 0
        assert _backups(db) == []

    def test_a_database_from_before_the_migration_table_is_backed_up_as_all_pending(self, current_db):
        con = sqlite3.connect(current_db)
        con.execute("DROP TABLE schema_migration")
        con.commit()
        con.close()
        r = _start(current_db)
        assert r.returncode == 0, r.stderr
        assert [b.name for b in _backups(current_db)] == [f"pmas.db.pre-{FIRST}.bak"]
        assert LAST in _versions(current_db)

    def test_a_second_start_after_a_failed_one_keeps_the_first_backup(self, current_db):
        _rewind(current_db, LAST)
        _start(current_db)
        (backup,) = _backups(current_db)
        stamp = backup.stat().st_mtime_ns
        _rewind(current_db, LAST)
        _start(current_db)
        assert [b.name for b in _backups(current_db)] == [backup.name]
        assert backup.stat().st_mtime_ns == stamp                  # not replaced


class TestBackupFailureStopsStartup:
    def test_an_unusable_backup_target_stops_startup_and_changes_nothing(self, current_db):
        _rewind(current_db, LAST)
        (current_db.parent / f"pmas.db.pre-{LAST}.bak").mkdir()     # a folder in the way: VACUUM INTO cannot write
        r = _start(current_db)
        assert r.returncode != 0
        assert "backup" in r.stderr.lower() and "pmas.db" in r.stderr
        assert LAST not in _versions(current_db)                    # no migration ran


class TestRetention:
    def test_only_the_newest_backups_are_kept(self, current_db):
        old = []
        for i in range(7):
            f = current_db.parent / f"pmas.db.pre-M0{i:02d}_old.bak"
            f.write_text("old")
            os.utime(f, (time.time() - 10_000 + i, time.time() - 10_000 + i))
            old.append(f)
        _rewind(current_db, LAST)
        _start(current_db)
        kept = _backups(current_db)
        assert len(kept) == 5
        assert any(b.name == f"pmas.db.pre-{LAST}.bak" for b in kept)   # the new one is kept
        assert not old[0].exists() and not old[1].exists() and not old[2].exists()

    def test_the_limit_can_be_changed_by_environment(self, current_db):
        for i in range(4):
            f = current_db.parent / f"pmas.db.pre-M0{i:02d}_old.bak"
            f.write_text("old")
            os.utime(f, (time.time() - 10_000 + i, time.time() - 10_000 + i))
        _rewind(current_db, LAST)
        _start(current_db, {"PMAS_MIGRATION_BACKUPS_KEEP": "2"})
        assert len(_backups(current_db)) == 2


class TestMigrationList:
    def test_the_list_matches_the_migrations_in_the_code(self):
        """A migration that is not in the list would run without a backup."""
        from backend.app import database
        source = (ROOT / "backend" / "app" / "database.py").read_text(encoding="utf-8")
        in_code = re.findall(r'_applied\(conn, "(M\d+_[a-z0-9_]+)"\)', source)
        assert in_code, "no migration found: the check is broken"
        assert list(database._MIGRATION_IDS) == in_code
        assert in_code == sorted(in_code)                           # ids grow in order
        assert len(set(in_code)) == len(in_code)
