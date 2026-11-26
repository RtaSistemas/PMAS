"""The JWT signing key in production (WO-001 T2).

The key is read when backend.app.deps is imported, so each case runs in a new Python process.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
KEY_VAR = "PMAS_SECRET_KEY"


def _import_deps(env_extra: dict[str, str]) -> subprocess.CompletedProcess:
    """Import backend.app.deps in a clean process with only the given PMAS_* variables."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("PMAS_")}
    env["PMAS_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "k.db")
    env.update(env_extra)
    code = "import backend.app.deps as d; print('KEYLEN', len(d.SECRET_KEY))"
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True)


class TestProductionNeedsAFixedKey:
    def test_production_without_a_key_stops_at_startup(self):
        r = _import_deps({"PMAS_ENV": "production"})
        assert r.returncode != 0
        assert "RuntimeError" in r.stderr
        assert KEY_VAR in r.stderr                     # the message names the variable to set

    def test_production_with_an_empty_key_stops(self):
        assert _import_deps({"PMAS_ENV": "production", KEY_VAR: ""}).returncode != 0

    def test_production_with_a_short_key_stops(self):
        r = _import_deps({"PMAS_ENV": "production", KEY_VAR: "x" * 16})
        assert r.returncode != 0 and "32" in r.stderr

    def test_production_with_a_key_of_only_spaces_stops(self):
        assert _import_deps({"PMAS_ENV": "production", KEY_VAR: " " * 40}).returncode != 0

    def test_production_with_a_32_character_key_starts(self):
        r = _import_deps({"PMAS_ENV": "production", KEY_VAR: "k" * 32})
        assert r.returncode == 0, r.stderr
        assert "KEYLEN 32" in r.stdout

    def test_production_with_a_64_character_key_starts_and_uses_it(self):
        r = _import_deps({"PMAS_ENV": "production", KEY_VAR: "k" * 64})
        assert r.returncode == 0, r.stderr
        assert "KEYLEN 64" in r.stdout

    def test_production_value_is_not_case_sensitive(self):
        assert _import_deps({"PMAS_ENV": " Production "}).returncode != 0


class TestDevelopmentKeepsTheOldBehavior:
    def test_development_without_a_key_starts_with_a_warning(self):
        r = _import_deps({})
        assert r.returncode == 0, r.stderr
        assert "KEYLEN" in r.stdout
        assert KEY_VAR in r.stderr                     # the old warning still names the variable

    def test_explicit_development_without_a_key_starts(self):
        assert _import_deps({"PMAS_ENV": "development"}).returncode == 0

    def test_development_accepts_a_short_key(self):
        r = _import_deps({KEY_VAR: "short"})
        assert r.returncode == 0 and "KEYLEN 5" in r.stdout

    def test_an_unknown_environment_name_counts_as_development(self):
        """run.py treats every value except 'production' as development; the key check does the same."""
        assert _import_deps({"PMAS_ENV": "staging"}).returncode == 0


@pytest.mark.parametrize("length", [31, 32])
def test_the_limit_is_exactly_32_characters(length):
    r = _import_deps({"PMAS_ENV": "production", KEY_VAR: "k" * length})
    assert (r.returncode == 0) == (length >= 32)
