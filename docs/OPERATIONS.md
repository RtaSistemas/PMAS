# PMAS Operations Guide (Linux)

This guide tells you how to install and operate PMAS on a Linux server from the standalone binary.
The profile in `docs/STE-GUIDE.md` (ASD-STE100) governs the text of this guide.

## What you need

- A Linux server with systemd (for example Ubuntu 22.04 or Debian 12).
- Root access (sudo).
- The package `pmas-linux-x64-package.tar.gz` from the GitHub Release.
- A reverse proxy with HTTPS in front of PMAS for access from the network.

## Install

1. Unpack the package: `tar -xzf pmas-linux-x64-package.tar.gz`
2. Go into the folder: `cd pmas-linux-x64-package`
3. Run the installer: `sudo ./install.sh`

The installer does these steps:

| Step | Result |
|------|--------|
| Create the user `pmas` | The service runs without root rights |
| Copy the program | `/opt/pmas/pmas` |
| Create the settings file | `/etc/pmas/pmas.env` |
| Create the data folders | `/var/lib/pmas` (database and backups), `/var/log/pmas` (logs) |
| Install the service | `pmas.service` starts at boot and restarts after an error |
| Install the backup timer | `pmas-backup.timer` makes a backup every day at 02:00 |

After the installation, open `http://127.0.0.1:8765`.

The installer makes a random password of 20 characters for the user `admin` and shows it **once** on the terminal.
Write the password down. PMAS does not save it and does not show it again. PMAS asks for a new password at the first login.

How the password reaches PMAS:

1. The installer writes `PMAS_ADMIN_INITIAL_PASSWORD` in `/etc/pmas/pmas.env` for the first start.
2. PMAS creates the `admin` account with that password when the database has no user.
3. The installer waits until `GET /ready` answers, and then removes the line from the settings file.

PMAS does not write the password in a log or in the journal. In production PMAS refuses to create the `admin` account without this variable, and it never creates a known default password.
If the service does not answer in 60 seconds, the installer tells you. The line stays in the file until the first good start. Remove it then.

For a manual first start in production, set `PMAS_ADMIN_INITIAL_PASSWORD` (6 characters or more, 72 bytes or less), start PMAS once, and remove the variable.
An update with `./install.sh` never creates or changes this password. An old installation can still have the password `admin`: PMAS writes a warning in the log at each start until the password changes. Change it in the Admin tab.

## Daily commands

| Task | Command |
|------|---------|
| See the state | `sudo systemctl status pmas` |
| Start | `sudo systemctl start pmas` |
| Stop | `sudo systemctl stop pmas` |
| Restart | `sudo systemctl restart pmas` |
| Read the logs | `sudo journalctl -u pmas -f` or `tail -f /var/log/pmas/pmas.log` |
| Check the health | `curl -s http://127.0.0.1:8765/health` |
| Check the database | `curl -s http://127.0.0.1:8765/ready` |

## Change the settings

1. Edit `/etc/pmas/pmas.env`. The file has a comment for each setting.
2. Restart the service: `sudo systemctl restart pmas`

| Setting | Meaning | Default |
|---------|---------|---------|
| `PMAS_ENV` | `production` makes PMAS refuse to start without a JWT signing key. The installer sets it. | `production` in the package |
| `PMAS_SECRET_KEY` | The JWT signing key. 32 characters or more. The installer makes a random key. | made by the installer |
| `PMAS_HOST` | Address that PMAS listens on. Use `0.0.0.0` only when no reverse proxy is in front. | `127.0.0.1` |
| `PMAS_PORT` | Port | `8765` |
| `PMAS_DB_PATH` | Database file | `/var/lib/pmas/pmas.db` |
| `PMAS_LOG_FILE` | Log file | `/var/log/pmas/pmas.log` |
| `PMAS_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING` or `ERROR` | `INFO` |
| `PMAS_MAX_UPLOAD_MB` | Maximum size of an import file | `20` |
| `PMAS_UPLOAD_RATE_LIMIT` | Imports for each minute | `60/minute` |
| `PMAS_ALLOWED_ORIGINS` | Addresses that browsers use to open PMAS | none |
| `PMAS_BACKUP_DIR` | Backup folder | `/var/lib/pmas/backups` |
| `PMAS_BACKUP_RETENTION` | Days to keep a backup | `30` |

## Update to a new version

1. Download and unpack the new package.
2. Make a backup: `sudo systemctl start pmas-backup.service`
3. Run the installer again: `sudo ./install.sh`

The installer stops the service, replaces the program, and starts the service again.
It keeps `/etc/pmas/pmas.env` and the database. PMAS updates the database structure at start.

## Backup and restore

The backup timer saves a consistent copy of the database every day. The files are in `/var/lib/pmas/backups`.
To make a backup now, run `sudo systemctl start pmas-backup.service`.
To see the timer, run `systemctl list-timers pmas-backup.timer`.

To restore a backup:

1. Stop the service: `sudo systemctl stop pmas`
2. Copy the backup over the database: `sudo cp /var/lib/pmas/backups/pmas_YYYY-MM-DDTHHMMSS.db /var/lib/pmas/pmas.db`
3. Set the owner: `sudo chown pmas:pmas /var/lib/pmas/pmas.db`
4. Delete the old journal files if they exist: `sudo rm -f /var/lib/pmas/pmas.db-wal /var/lib/pmas/pmas.db-shm`
5. Start the service: `sudo systemctl start pmas`
6. Check the health: `curl -s http://127.0.0.1:8765/health`

Copy the backup folder to a second server or storage. A backup on the same disk does not protect you from a disk failure.

## Change the JWT signing key

The installer makes a random key and writes it in `/etc/pmas/pmas.env`. The key signs the login tokens.
A restart does not change the key, so users stay logged in after a restart or an update.

To change the key:

1. Make a new key: `openssl rand -base64 48`
2. Replace the value of `PMAS_SECRET_KEY` in `/etc/pmas/pmas.env`. Use 32 characters or more.
3. Restart the service: `sudo systemctl restart pmas`

The effect: every token that PMAS issued before the change stops working, and every user must log in again.
Change the key when you think that someone else knows it.
In production, PMAS does not start without a key of 32 characters or more. The log then shows a clear message.

An update with `./install.sh` adds a key to an old settings file that has none, and then every user must log in again once.
The installer never replaces a key that exists. It stops the update when the key in the file has fewer than 32 characters.

## Reverse proxy

PMAS listens on `127.0.0.1` and does not use HTTPS by itself. Put a reverse proxy (for example nginx or Caddy) in front of it.
Set `PMAS_ALLOWED_ORIGINS` to the public address, for example `https://pmas.example.com`.
Set the upload size limit of the proxy to a value that is equal to or larger than `PMAS_MAX_UPLOAD_MB`.

## Remove PMAS

Run `sudo ./install.sh uninstall`. The command removes the service and the program.
It does not remove the data in `/var/lib/pmas` or the settings in `/etc/pmas`.

## If something is wrong

| Problem | Cause | Action |
|---------|-------|--------|
| The service does not start | The settings file has an error, or the port is in use | Read the logs. Change `PMAS_PORT` if another program uses the port. |
| The service stops at start and the log shows a permission error | The data folder has the wrong owner | Run `sudo chown -R pmas:pmas /var/lib/pmas /var/log/pmas` |
| The binary does not run (`Permission denied` for a temporary file) | The `/tmp` folder does not allow programs to run | Mount `/tmp` without `noexec`, or set `TMPDIR` for the service to another folder |
| The service stops at start with "PMAS cannot use the database path" | The folder of `PMAS_DB_PATH` cannot be created or written | Fix the path or the owner of the folder. PMAS creates a missing folder when it can. |
| The log shows "Cannot write the log file" | The folder of `PMAS_LOG_FILE` cannot be written | Fix the path or the owner. PMAS writes to the console (journal) until then. |
| `/ready` returns 503 | The database file is not available | Check `PMAS_DB_PATH` and the owner of the file |
| An import returns 413 | The file is larger than the limit | Increase `PMAS_MAX_UPLOAD_MB` and the limit of the reverse proxy |
| A user cannot log in after 5 errors | The account is locked for 15 minutes | Wait, or ask an administrator to set a new password |
