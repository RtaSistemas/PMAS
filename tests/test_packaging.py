"""Linux install package: build, install, update, uninstall and the backup script.

The tests run the real shell scripts in temporary folders. PMAS_SKIP_SYSTEM=1 stops the
installer from creating a user or calling systemctl.
"""
from __future__ import annotations

import configparser
import os
import shutil
import sqlite3
import subprocess
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required")


def _run(args, env=None, cwd=None, check=True):
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(args, env=full_env, cwd=cwd, capture_output=True, text=True, check=check)


@pytest.fixture()
def package(tmp_path):
    binary = tmp_path / "fake-pmas"
    binary.write_text("#!/bin/sh\necho version-1\n")
    out = tmp_path / "dist"
    result = _run([str(ROOT / "packaging/build_package.sh"), str(binary), str(out)])
    archive = Path(result.stdout.strip())
    with tarfile.open(archive) as tar:
        tar.extractall(tmp_path / "unpacked", filter="data")
    return tmp_path / "unpacked" / "pmas-linux-x64-package", archive, binary


def _paths(tmp_path):
    return {
        "PMAS_SKIP_SYSTEM": "1",
        "PMAS_PREFIX": str(tmp_path / "opt"),
        "PMAS_ETC": str(tmp_path / "etc"),
        "PMAS_DATA": str(tmp_path / "var-lib"),
        "PMAS_LOGDIR": str(tmp_path / "var-log"),
        "PMAS_SYSTEMD_DIR": str(tmp_path / "units"),
    }


def test_package_has_every_file(package):
    folder, archive, _ = package
    names = {p.name for p in folder.iterdir()}
    assert names == {"pmas", "install.sh", "backup_pmas.sh", "pmas.service", "pmas-backup.service",
                     "pmas-backup.timer", "pmas.env.example", "OPERATIONS.md"}
    assert archive.name == "pmas-linux-x64-package.tar.gz"


def test_build_fails_without_a_binary(tmp_path):
    r = _run([str(ROOT / "packaging/build_package.sh"), str(tmp_path / "missing")], check=False)
    assert r.returncode != 0


def test_install_copies_files_and_rewrites_paths(package, tmp_path):
    folder, _, _ = package
    env = _paths(tmp_path)
    _run([str(folder / "install.sh")], env=env, cwd=folder)

    opt = Path(env["PMAS_PREFIX"])
    assert os.access(opt / "pmas", os.X_OK)
    assert os.access(opt / "backup_pmas.sh", os.X_OK)
    assert (Path(env["PMAS_DATA"]) / "backups").is_dir()
    assert Path(env["PMAS_LOGDIR"]).is_dir()

    env_file = Path(env["PMAS_ETC"]) / "pmas.env"
    text = env_file.read_text()
    assert f"PMAS_DB_PATH={env['PMAS_DATA']}/pmas.db" in text
    assert f"PMAS_LOG_FILE={env['PMAS_LOGDIR']}/pmas.log" in text
    assert oct(env_file.stat().st_mode & 0o777) == "0o640"

    service = (Path(env["PMAS_SYSTEMD_DIR"]) / "pmas.service").read_text()
    assert f"ExecStart={env['PMAS_PREFIX']}/pmas" in service
    assert f"EnvironmentFile=-{env['PMAS_ETC']}/pmas.env" in service
    assert f"WorkingDirectory={env['PMAS_DATA']}" in service
    assert f"ReadWritePaths={env['PMAS_DATA']} {env['PMAS_LOGDIR']}" in service   # no default path stays


def test_installed_units_are_valid(package, tmp_path):
    folder, _, _ = package
    env = _paths(tmp_path)
    _run([str(folder / "install.sh")], env=env, cwd=folder)
    for name, required in (("pmas.service", ("Service", "ExecStart")),
                           ("pmas-backup.service", ("Service", "ExecStart")),
                           ("pmas-backup.timer", ("Timer", "OnCalendar"))):
        cp = configparser.ConfigParser(strict=False, interpolation=None)
        cp.optionxform = str
        cp.read(Path(env["PMAS_SYSTEMD_DIR"]) / name)
        assert cp.has_option(*required), name
    service = configparser.ConfigParser(strict=False, interpolation=None)
    service.optionxform = str
    service.read(Path(env["PMAS_SYSTEMD_DIR"]) / "pmas.service")
    assert service["Service"]["Restart"] == "on-failure"
    assert service["Install"]["WantedBy"] == "multi-user.target"
    # systemd reads the start limit keys in [Unit]; in [Service] it ignores them.
    assert service.has_option("Unit", "StartLimitIntervalSec")
    assert not service.has_option("Service", "StartLimitIntervalSec")


def test_update_replaces_the_binary_and_keeps_the_settings(package, tmp_path):
    folder, _, _ = package
    env = _paths(tmp_path)
    _run([str(folder / "install.sh")], env=env, cwd=folder)

    env_file = Path(env["PMAS_ETC"]) / "pmas.env"
    env_file.write_text(env_file.read_text() + "\nPMAS_PORT=9999\n")
    (Path(env["PMAS_DATA"]) / "pmas.db").write_text("data")

    new_binary = tmp_path / "pmas-v2"
    new_binary.write_text("#!/bin/sh\necho version-2\n")
    _run([str(folder / "install.sh"), "install", str(new_binary)], env=env, cwd=folder)

    assert "version-2" in (Path(env["PMAS_PREFIX"]) / "pmas").read_text()
    assert "PMAS_PORT=9999" in env_file.read_text()               # settings kept
    assert (Path(env["PMAS_DATA"]) / "pmas.db").read_text() == "data"   # data kept


def test_install_fails_when_the_binary_is_missing(package, tmp_path):
    folder, _, _ = package
    (folder / "pmas").unlink()
    r = _run([str(folder / "install.sh")], env=_paths(tmp_path), cwd=folder, check=False)
    assert r.returncode != 0
    assert "Binary not found" in r.stderr


def test_uninstall_removes_the_program_and_keeps_the_data(package, tmp_path):
    folder, _, _ = package
    env = _paths(tmp_path)
    _run([str(folder / "install.sh")], env=env, cwd=folder)
    (Path(env["PMAS_DATA"]) / "pmas.db").write_text("data")
    _run([str(folder / "install.sh"), "uninstall"], env=env, cwd=folder)

    assert not Path(env["PMAS_PREFIX"]).exists()
    assert not (Path(env["PMAS_SYSTEMD_DIR"]) / "pmas.service").exists()
    assert (Path(env["PMAS_DATA"]) / "pmas.db").exists()
    assert (Path(env["PMAS_ETC"]) / "pmas.env").exists()


def _tool_dir(tmp_path, with_sqlite3: bool) -> Path:
    """A PATH folder with only the tools that the backup script needs."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    tools = ["date", "du", "cut", "find", "wc", "mkdir", "python3", "env"]
    if with_sqlite3:
        tools.append("sqlite3")
    for tool in tools:
        found = shutil.which(tool)
        if found:
            (bin_dir / tool).symlink_to(found)
    return bin_dir


@pytest.mark.parametrize("with_sqlite3", [True, False])
def test_backup_script_makes_a_valid_copy(tmp_path, with_sqlite3):
    if with_sqlite3 and shutil.which("sqlite3") is None:
        pytest.skip("the sqlite3 program is not installed")
    db = tmp_path / "pmas.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE t (x INTEGER)")
    con.execute("INSERT INTO t VALUES (42)")
    con.commit()
    con.close()

    backups = tmp_path / "backups"
    bin_dir = _tool_dir(tmp_path, with_sqlite3)
    bash = shutil.which("bash")
    r = _run([bash, str(ROOT / "backup_pmas.sh"), str(db), str(backups)], env={"PATH": str(bin_dir)})
    assert "Backup complete" in r.stdout

    copies = list(backups.glob("pmas_*.db"))
    assert len(copies) == 1
    assert sqlite3.connect(copies[0]).execute("SELECT x FROM t").fetchone() == (42,)


def test_backup_script_fails_for_a_missing_database(tmp_path):
    r = _run(["bash", str(ROOT / "backup_pmas.sh"), str(tmp_path / "none.db"), str(tmp_path / "b")], check=False)
    assert r.returncode != 0
    assert "database not found" in r.stderr


def test_install_rejects_a_path_with_a_space(package, tmp_path):
    """A space in a path would split ExecStart and ReadWritePaths in the unit files."""
    folder, _, _ = package
    env = _paths(tmp_path)
    env["PMAS_PREFIX"] = str(tmp_path / "opt dir")
    r = _run([str(folder / "install.sh")], env=env, cwd=folder, check=False)
    assert r.returncode != 0
    assert "space" in r.stderr
    assert not (tmp_path / "units" / "pmas.service").exists()
