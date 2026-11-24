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

cmd_install() {
  as_root
  local binary; binary="$(find_binary "${1:-}")"
  [[ -f "$binary" ]] || fail "Binary not found: $binary"

  if [[ "$SKIP" != "1" ]]; then
    id pmas &>/dev/null || { useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin pmas; log "Created the user pmas."; }
  fi

  mkdir -p "$PREFIX" "$ETC" "$DATA/backups" "$LOGDIR" "$UNITS"
  local was_running=0
  if [[ "$SKIP" != "1" ]] && systemctl is-active --quiet pmas 2>/dev/null; then
    was_running=1; systemctl stop pmas
  fi

  install -m 0755 "$binary" "$PREFIX/pmas"
  install -m 0755 "$HERE/backup_pmas.sh" "$PREFIX/backup_pmas.sh"
  log "Installed the binary in $PREFIX."

  if [[ ! -f "$ETC/pmas.env" ]]; then
    sed -e "s#/var/lib/pmas#$DATA#g" -e "s#/var/log/pmas#$LOGDIR#g" \
        "$HERE/pmas.env.example" > "$ETC/pmas.env"
    chmod 0640 "$ETC/pmas.env"
    log "Created $ETC/pmas.env. Edit this file to change the settings."
  else
    log "Kept the settings in $ETC/pmas.env."
  fi

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
