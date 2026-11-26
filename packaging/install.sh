#!/usr/bin/env bash
# Install or update PMAS as a systemd service from the standalone Linux binary.
#
#   sudo ./install.sh [install] [PATH_TO_BINARY]   install, or replace the binary and restart
#   sudo ./install.sh uninstall                    remove the service; the data stays
#
# The default binary is "pmas" or "pmas-linux-x64" next to this script.
# Run the script again with a new binary to update. It keeps /etc/pmas/pmas.env and the data.
#
# The paths can change with PMAS_PREFIX, PMAS_ETC, PMAS_DATA, PMAS_LOGDIR and PMAS_SYSTEMD_DIR.
# Set PMAS_SKIP_SYSTEM=1 to copy files only (no user, no systemctl). The tests use this.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PMAS_PREFIX:-/opt/pmas}"
ETC="${PMAS_ETC:-/etc/pmas}"
DATA="${PMAS_DATA:-/var/lib/pmas}"
LOGDIR="${PMAS_LOGDIR:-/var/log/pmas}"
UNITS="${PMAS_SYSTEMD_DIR:-/etc/systemd/system}"
SKIP="${PMAS_SKIP_SYSTEM:-0}"

MIN_KEY_LENGTH=32

log()  { echo "[pmas-install] $*"; }
fail() { echo "[pmas-install] ERROR: $*" >&2; exit 1; }

as_root() {
  [[ "$SKIP" == "1" || $EUID -eq 0 ]] || fail "Run this script as root (use sudo)."
}

systemctl_do() { [[ "$SKIP" == "1" ]] || systemctl "$@"; }

find_binary() {
  local given="${1:-}"
  if [[ -n "$given" ]]; then echo "$given"; return; fi
  for name in pmas pmas-linux-x64; do
    [[ -f "$HERE/$name" ]] && { echo "$HERE/$name"; return; }
  done
  fail "Binary not found. Give the path: ./install.sh install /path/to/pmas-linux-x64"
}

# The unit files name /opt/pmas, /etc/pmas, /var/lib/pmas and /var/log/pmas.
# When the paths change, write the changed paths into the installed copy.
install_unit() {
  local name="$1"
  sed -e "s#/opt/pmas#$PREFIX#g" -e "s#/etc/pmas#$ETC#g" \
      -e "s#/var/lib/pmas#$DATA#g" -e "s#/var/log/pmas#$LOGDIR#g" \
      "$HERE/$name" > "$UNITS/$name"
  chmod 0644 "$UNITS/$name"
}

# --- settings file helpers (the JWT signing key and the mode) -------------------------------------
# Value of KEY in the settings file, or an empty text when the line is missing or empty.
get_env() {
  [[ -f "$ETC/pmas.env" ]] || return 0
  { grep -E "^$1=" "$ETC/pmas.env" || true; } | tail -n 1 | cut -d= -f2-
}

# Set KEY=VALUE. A changed value replaces the old line. The file keeps its owner and mode.
set_env() {
  local file="$ETC/pmas.env" tmp
  tmp="$(mktemp)"
  { grep -v -E "^$1=" "$file" || true; } > "$tmp"
  printf '%s=%s\n' "$1" "$2" >> "$tmp"
  cat "$tmp" > "$file"
  rm -f "$tmp"
}

# A random key of at least MIN_KEY_LENGTH characters. A server with only the binary can lack
# openssl and python3, so the last choice is /dev/urandom.
generate_key() {
  local key=""
  if command -v openssl >/dev/null 2>&1; then
    key="$(openssl rand -base64 48 | tr -d '\n')"
  elif command -v python3 >/dev/null 2>&1; then
    key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  else
    key="$(head -c 48 /dev/urandom | base64 | tr -d '\n')"
  fi
  [[ ${#key} -ge $MIN_KEY_LENGTH ]] || fail "Could not make a random key."
  printf '%s' "$key"
}

# An existing key that is too short stops the update before PMAS changes anything,
# because production mode would refuse to start with it.
check_existing_key() {
  local key mode
  key="$(get_env PMAS_SECRET_KEY)"; mode="$(get_env PMAS_ENV)"
  if [[ -n "$key" && ${#key} -lt $MIN_KEY_LENGTH && "${mode:-production}" == "production" ]]; then
    fail "The key in $ETC/pmas.env has ${#key} characters. Production needs $MIN_KEY_LENGTH or more. Replace the key, then run this script again."
  fi
}

# Make sure the settings file has a key and a mode. Never replace an existing key.
ensure_jwt_key() {
  local fresh="${1:-}" added=0
  if [[ -z "$(get_env PMAS_SECRET_KEY)" ]]; then
    set_env PMAS_SECRET_KEY "$(generate_key)"
    added=1
  fi
  [[ -n "$(get_env PMAS_ENV)" ]] || set_env PMAS_ENV production
  chmod 0640 "$ETC/pmas.env"
  if [[ $added -eq 1 && "$fresh" == "new" ]]; then
    log "Created a JWT signing key in $ETC/pmas.env."
  elif [[ $added -eq 1 ]]; then
    log "Added a JWT signing key to $ETC/pmas.env. Every user must log in again once."
  else
    log "Kept the JWT signing key in $ETC/pmas.env."
  fi
}

cmd_install() {
  as_root
  local binary; binary="$(find_binary "${1:-}")"
  [[ -f "$binary" ]] || fail "Binary not found: $binary"

  # A space or one of # & in a path breaks the unit files (ExecStart splits at a space).
  local p
  for p in "$PREFIX" "$ETC" "$DATA" "$LOGDIR"; do
    case "$p" in
      *[[:space:]\#\&]*) fail "The path \"$p\" has a space, # or &. Use a path without them." ;;
    esac
  done

  if [[ "$SKIP" != "1" ]]; then
    id pmas &>/dev/null || { useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin pmas; log "Created the user pmas."; }
  fi

  check_existing_key

  mkdir -p "$PREFIX" "$ETC" "$DATA/backups" "$LOGDIR" "$UNITS"
  local was_running=0
  if [[ "$SKIP" != "1" ]] && systemctl is-active --quiet pmas 2>/dev/null; then
    was_running=1; systemctl stop pmas
  fi

  install -m 0755 "$binary" "$PREFIX/pmas"
  install -m 0755 "$HERE/backup_pmas.sh" "$PREFIX/backup_pmas.sh"
  log "Installed the binary in $PREFIX."

  local env_is_new=""
  if [[ ! -f "$ETC/pmas.env" ]]; then
    env_is_new="new"
    sed -e "s#/var/lib/pmas#$DATA#g" -e "s#/var/log/pmas#$LOGDIR#g" \
        "$HERE/pmas.env.example" > "$ETC/pmas.env"
    chmod 0640 "$ETC/pmas.env"
    log "Created $ETC/pmas.env. Edit this file to change the settings."
  else
    log "Kept the settings in $ETC/pmas.env."
  fi
  ensure_jwt_key "$env_is_new"

  if [[ "$SKIP" != "1" ]]; then
    chown -R pmas:pmas "$DATA" "$LOGDIR"
    chown root:pmas "$ETC/pmas.env"
  fi

  for unit in pmas.service pmas-backup.service pmas-backup.timer; do install_unit "$unit"; done

  systemctl_do daemon-reload
  systemctl_do enable pmas.service pmas-backup.timer
  systemctl_do restart pmas.service
  systemctl_do start pmas-backup.timer
  [[ $was_running -eq 1 ]] && log "Updated and restarted the service." || log "Started the service."

  local port; port="$(grep -E '^PMAS_PORT=' "$ETC/pmas.env" | cut -d= -f2 || true)"
  log "Check it with: curl -s http://127.0.0.1:${port:-8765}/health"
  log "First login: user admin, password admin. PMAS asks for a new password."
}

cmd_uninstall() {
  as_root
  systemctl_do disable --now pmas.service pmas-backup.timer 2>/dev/null || true
  rm -f "$UNITS/pmas.service" "$UNITS/pmas-backup.service" "$UNITS/pmas-backup.timer"
  rm -rf "$PREFIX"
  systemctl_do daemon-reload
  log "Removed the service and the program. The data stays in $DATA and the settings in $ETC."
}

case "${1:-install}" in
  install)   shift || true; cmd_install "${1:-}" ;;
  uninstall) cmd_uninstall ;;
  *)         # a path as the first argument means install
             [[ -f "${1:-}" ]] && cmd_install "$1" || fail "Use: install [PATH_TO_BINARY] | uninstall" ;;
esac
