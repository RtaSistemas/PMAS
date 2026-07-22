#!/usr/bin/env bash
# PMAS deployment script — installs or updates PMAS on a Linux server.
# Tested on Ubuntu 22.04 / Debian 12.
#
# Usage:
#   sudo bash deploy.sh [install|update|status|logs|stop|restart]
#
# The default action (no argument) runs 'install' on a fresh machine
# or 'update' if /opt/pmas already exists.

set -euo pipefail

APP_DIR=/opt/pmas
SERVICE=pmas
PYTHON=${PYTHON:-python3.11}
REPO_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_log()  { echo "[$(date '+%H:%M:%S')] $*"; }
_ok()   { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
_err()  { echo "[$(date '+%H:%M:%S')] ✗ $*" >&2; exit 1; }

require_root() {
  [[ $EUID -eq 0 ]] || _err "Execute como root: sudo bash $0 $*"
}

install_deps() {
  _log "Instalando dependências do sistema..."
  apt-get update -qq
  apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-distutils \
    curl ca-certificates sqlite3 \
    > /dev/null
  _ok "Dependências instaladas."
}

create_user() {
  if ! id pmas &>/dev/null; then
    useradd -r -s /sbin/nologin -d "$APP_DIR" -c "PMAS service account" pmas
    _ok "Utilizador 'pmas' criado."
  fi
}

setup_dirs() {
  mkdir -p "$APP_DIR" /var/log/pmas
  chown pmas:pmas "$APP_DIR" /var/log/pmas
  chmod 750 "$APP_DIR" /var/log/pmas
  _ok "Diretórios criados."
}

deploy_code() {
  _log "Copiando ficheiros da aplicação..."
  rsync -a --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='pmas.db' \
    --exclude='*.log' \
    --exclude='amostras' \
    --exclude='tests' \
    --exclude='node_modules' \
    "$REPO_SRC/" "$APP_DIR/"
  _ok "Código copiado para $APP_DIR."
}

setup_venv() {
  _log "Configurando ambiente virtual Python..."
  if [[ ! -d "$APP_DIR/.venv" ]]; then
    $PYTHON -m venv "$APP_DIR/.venv"
  fi
  "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
  "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements-lock.txt"
  chown -R pmas:pmas "$APP_DIR/.venv"
  _ok "Ambiente virtual configurado."
}

setup_env() {
  if [[ ! -f "$APP_DIR/.env" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    chown pmas:pmas "$APP_DIR/.env"
    _log "Ficheiro .env criado em $APP_DIR/.env — edite antes de iniciar o serviço."
  fi
}

install_service() {
  cp "$APP_DIR/pmas.service" /etc/systemd/system/pmas.service
  systemctl daemon-reload
  systemctl enable "$SERVICE"
  _ok "Serviço systemd instalado e activado."
}

cmd_install() {
  require_root
  install_deps
  create_user
  setup_dirs
  deploy_code
  setup_venv
  setup_env
  install_service
  _ok "Instalação concluída."
  echo ""
  echo "  Próximos passos:"
  echo "  1. Edite $APP_DIR/.env com as suas configurações"
  echo "  2. sudo systemctl start pmas"
  echo "  3. sudo systemctl status pmas"
  echo ""
}

cmd_update() {
  require_root
  _log "Actualizando PMAS..."
  deploy_code
  setup_venv
  install_service
  systemctl restart "$SERVICE"
  _ok "Actualização concluída. Serviço reiniciado."
}

cmd_status() {
  systemctl status "$SERVICE" --no-pager
}

cmd_logs() {
  journalctl -u "$SERVICE" -f --no-hostname
}

cmd_stop()    { require_root; systemctl stop    "$SERVICE"; _ok "Serviço parado."; }
cmd_restart() { require_root; systemctl restart "$SERVICE"; _ok "Serviço reiniciado."; }

# Entrypoint
ACTION="${1:-}"
if [[ -z "$ACTION" ]]; then
  ACTION=$([[ -d "$APP_DIR" ]] && echo "update" || echo "install")
fi

case "$ACTION" in
  install) cmd_install ;;
  update)  cmd_update  ;;
  status)  cmd_status  ;;
  logs)    cmd_logs    ;;
  stop)    cmd_stop    ;;
  restart) cmd_restart ;;
  *) echo "Uso: $0 [install|update|status|logs|stop|restart]"; exit 1 ;;
esac
