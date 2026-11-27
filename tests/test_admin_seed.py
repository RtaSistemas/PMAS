"""The first administrator account (WO-001 T3).

Development and tests keep admin/admin. Production seeds the account only from
PMAS_ADMIN_INITIAL_PASSWORD, and refuses to seed a known default password.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import bcrypt

ROOT = Path(__file__).resolve().parent.parent
PASSWORD_VAR = "PMAS_ADMIN_INITIAL_PASSWORD"
GOOD = "Xk3-Initial-Pass-9"


def _init_db(db_path: Path, env_extra: dict[str, str]) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("PMAS_")}
    env["PMAS_DB_PATH"] = str(db_path)
    env.update(env_extra)
    code = "from backend.app.database import init_db; init_db()"
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)


def _users(db_path: Path):
    if not db_path.exists():
        return []
    con = sqlite3.connect(db_path)
    try:
        return con.execute('SELECT username, hashed_password, role, must_change_password FROM "user"').fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


def _db() -> Path:
    return Path(tempfile.mkdtemp()) / "seed.db"


def _checks(hashed: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class TestProduction:
    def test_without_the_variable_startup_fails_and_no_user_is_created(self):
        db = _db()
        r = _init_db(db, {"PMAS_ENV": "production"})
        assert r.returncode != 0
        assert "RuntimeError" in r.stderr and PASSWORD_VAR in r.stderr
        assert _users(db) == []

    def test_with_the_variable_the_admin_gets_that_password_and_must_change_it(self):
        db = _db()
        r = _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: GOOD})
        assert r.returncode == 0, r.stderr
        (username, hashed, role, must_change), = _users(db)
        assert (username, role, must_change) == ("admin", "admin", 1)
        assert _checks(hashed, GOOD)
        assert not _checks(hashed, "admin")                      # the old default does not work

    def test_the_password_is_never_written_to_the_output(self):
        r = _init_db(_db(), {"PMAS_ENV": "production", PASSWORD_VAR: GOOD})
        assert GOOD not in r.stdout and GOOD not in r.stderr

    def test_a_password_shorter_than_6_characters_stops_startup(self):
        db = _db()
        r = _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: "abc"})
        assert r.returncode != 0 and _users(db) == []
        assert "abc" not in r.stderr.replace(PASSWORD_VAR, "")   # the message does not echo it

    def test_a_password_longer_than_72_bytes_stops_startup(self):
        db = _db()
        r = _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: "p" * 73})
        assert r.returncode != 0 and _users(db) == []

    def test_the_exact_default_password_is_refused(self):
        db = _db()
        r = _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: "admin123"})
        # only the exact default is blocked; a different long password is fine
        assert r.returncode == 0
        assert _init_db(_db(), {"PMAS_ENV": "production", PASSWORD_VAR: "admin"}).returncode != 0

    def test_a_restart_with_users_and_without_the_variable_starts(self):
        """The installer removes the variable after the first start: later restarts must work."""
        db = _db()
        assert _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: GOOD}).returncode == 0
        again = _init_db(db, {"PMAS_ENV": "production"})
        assert again.returncode == 0, again.stderr
        assert len(_users(db)) == 1

    def test_the_variable_does_not_change_an_existing_account(self):
        db = _db()
        _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: GOOD})
        _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: "Another-One-77"})
        (_, hashed, _, _), = _users(db)
        assert _checks(hashed, GOOD) and not _checks(hashed, "Another-One-77")

    def test_an_old_install_with_the_default_password_gets_a_warning(self):
        db = _db()
        assert _init_db(db, {}).returncode == 0                  # development seed: admin/admin
        r = _init_db(db, {"PMAS_ENV": "production"})
        assert r.returncode == 0, r.stderr
        assert "senha padrão" in r.stderr and "admin" in r.stderr

    def test_no_warning_after_the_password_changed(self):
        db = _db()
        _init_db(db, {"PMAS_ENV": "production", PASSWORD_VAR: GOOD})
        r = _init_db(db, {"PMAS_ENV": "production"})
        assert "senha padrão" not in r.stderr


class TestDevelopment:
    def test_development_still_seeds_admin_admin(self):
        db = _db()
        r = _init_db(db, {})
        assert r.returncode == 0, r.stderr
        (username, hashed, role, must_change), = _users(db)
        assert (username, role, must_change) == ("admin", "admin", 1)
        assert _checks(hashed, "admin")

    def test_explicit_development_ignores_the_variable(self):
        db = _db()
        _init_db(db, {"PMAS_ENV": "development", PASSWORD_VAR: GOOD})
        (_, hashed, _, _), = _users(db)
        assert _checks(hashed, "admin")
