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


# ---------------------------------------------------------------------------
# JWT signing key and PMAS_ENV in the installed settings file (WO-001 T2)
# ---------------------------------------------------------------------------

KEY_VAR = "PMAS_SECRET_KEY"


def _env_values(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in env_file.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k] = v
    return values


def _install(folder, tmp_path, *args, extra_env=None, check=True):
    env = {**_paths(tmp_path), **(extra_env or {})}
    return _run([str(folder / "install.sh"), *args], env=env, cwd=folder, check=check)


def _env_file(tmp_path) -> Path:
    return tmp_path / "etc" / "pmas.env"


class TestInstallerWritesTheJwtKey:
    def test_fresh_install_creates_a_key_and_production_mode(self, package, tmp_path):
        folder, _, _ = package
        r = _install(folder, tmp_path)
        values = _env_values(_env_file(tmp_path))
        assert len(values[KEY_VAR]) >= 32
        assert values["PMAS_ENV"] == "production"
        assert oct(_env_file(tmp_path).stat().st_mode & 0o777) == "0o640"
        assert values[KEY_VAR] not in r.stdout + r.stderr           # the installer never prints the key

    def test_two_installs_make_two_different_keys(self, package, tmp_path):
        folder, _, _ = package
        _install(folder, tmp_path)
        first = _env_values(_env_file(tmp_path))[KEY_VAR]
        other = tmp_path / "second"
        other.mkdir()
        _install(folder, other)
        assert _env_values(other / "etc" / "pmas.env")[KEY_VAR] != first

    def test_update_twice_keeps_the_same_key(self, package, tmp_path):
        folder, _, _ = package
        _install(folder, tmp_path)
        key = _env_values(_env_file(tmp_path))[KEY_VAR]
        _install(folder, tmp_path)
        _install(folder, tmp_path)
        text = _env_file(tmp_path).read_text()
        assert _env_values(_env_file(tmp_path))[KEY_VAR] == key
        assert len([line for line in text.splitlines() if line.startswith(f"{KEY_VAR}=")]) == 1
        assert len([line for line in text.splitlines() if line.startswith("PMAS_ENV=")]) == 1

    def test_update_on_an_old_settings_file_adds_the_key_and_keeps_the_rest(self, package, tmp_path):
        folder, _, _ = package
        env_file = _env_file(tmp_path)
        env_file.parent.mkdir(parents=True)
        env_file.write_text("PMAS_PORT=9999\nPMAS_LOG_LEVEL=DEBUG\n")
        env_file.chmod(0o640)
        r = _install(folder, tmp_path)
        values = _env_values(env_file)
        assert len(values[KEY_VAR]) >= 32
        assert values["PMAS_ENV"] == "production"
        assert values["PMAS_PORT"] == "9999" and values["PMAS_LOG_LEVEL"] == "DEBUG"
        assert oct(env_file.stat().st_mode & 0o777) == "0o640"
        assert "log in again" in (r.stdout + r.stderr).lower()       # one line about the effect

    def test_update_never_replaces_an_existing_key(self, package, tmp_path):
        folder, _, _ = package
        env_file = _env_file(tmp_path)
        env_file.parent.mkdir(parents=True)
        env_file.write_text(f"{KEY_VAR}={'k' * 40}\nPMAS_PORT=9999\n")
        _install(folder, tmp_path)
        values = _env_values(env_file)
        assert values[KEY_VAR] == "k" * 40
        assert values["PMAS_ENV"] == "production"

    def test_an_explicit_development_setting_is_kept(self, package, tmp_path):
        folder, _, _ = package
        env_file = _env_file(tmp_path)
        env_file.parent.mkdir(parents=True)
        env_file.write_text("PMAS_ENV=development\n")
        _install(folder, tmp_path)
        assert _env_values(env_file)["PMAS_ENV"] == "development"
        assert len(_env_values(env_file)[KEY_VAR]) >= 32

    def test_a_short_existing_key_stops_the_update_before_any_change(self, package, tmp_path):
        folder, _, _ = package
        env_file = _env_file(tmp_path)
        env_file.parent.mkdir(parents=True)
        env_file.write_text(f"{KEY_VAR}=short\nPMAS_PORT=9999\n")
        before = env_file.read_text()
        r = _install(folder, tmp_path, check=False)
        assert r.returncode != 0
        assert "32" in r.stderr
        assert env_file.read_text() == before                        # settings untouched
        assert not (tmp_path / "opt" / "pmas").exists()              # the program was not replaced

    def test_an_empty_key_line_counts_as_missing(self, package, tmp_path):
        folder, _, _ = package
        env_file = _env_file(tmp_path)
        env_file.parent.mkdir(parents=True)
        env_file.write_text(f"{KEY_VAR}=\n")
        _install(folder, tmp_path)
        assert len(_env_values(env_file)[KEY_VAR]) >= 32

    def test_the_installed_settings_satisfy_the_app_check(self, package, tmp_path):
        """The file that the installer writes must let the app start in production mode."""
        folder, _, _ = package
        _install(folder, tmp_path)
        env = {k: v for k, v in os.environ.items() if not k.startswith("PMAS_")}
        env.update(_env_values(_env_file(tmp_path)))
        env["PMAS_DB_PATH"] = str(tmp_path / "check.db")
        r = subprocess.run([os.sys.executable, "-c", "import backend.app.deps"],
                           cwd=ROOT, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    @pytest.mark.parametrize("hide", [("openssl",), ("openssl", "python3")])
    def test_key_generation_has_fallbacks(self, package, tmp_path, hide):
        """A server with only the binary may have no openssl, and no python3 either."""
        folder, _, _ = package
        tools = tmp_path / "tools"
        tools.mkdir()
        for name in ("bash", "env", "dirname", "sed", "grep", "cut", "install", "mkdir", "chmod", "cat",
                     "rm", "mktemp", "tr", "head", "base64", "id", "date", "python3", "openssl", "tail", "wc"):
            # Use the real program from /usr/bin or /bin: a sandbox can put a wrapper first in PATH.
            found = next((str(Path(d) / name) for d in ("/usr/bin", "/bin") if (Path(d) / name).exists()), None) \
                or shutil.which(name)
            if found and name not in hide:
                (tools / name).symlink_to(found)
        r = subprocess.run(["bash", str(folder / "install.sh")], env={**_paths(tmp_path), "PATH": str(tools)},
                           cwd=folder, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert len(_env_values(_env_file(tmp_path))[KEY_VAR]) >= 32


class TestEnvExample:
    def test_example_documents_both_variables_without_a_real_key(self):
        text = (ROOT / "packaging" / "pmas.env.example").read_text()
        values = _env_values(ROOT / "packaging" / "pmas.env.example")
        assert values["PMAS_ENV"] == "production"
        assert KEY_VAR in text
        assert values.get(KEY_VAR, "") == ""                         # no real key in the repository
