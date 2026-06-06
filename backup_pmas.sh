#!/usr/bin/env bash
# PMAS — SQLite backup script
# Uses VACUUM INTO for a consistent WAL-safe copy.
#
# Usage:
#   ./backup_pmas.sh [DB_PATH] [BACKUP_DIR]
#
# Defaults:
#   DB_PATH    — ./pmas.db
#   BACKUP_DIR — ./backups
#
# Cron (daily at 02:00):
#   0 2 * * * /opt/pmas/backup_pmas.sh >> /var/log/pmas_backup.log 2>&1
#
# Restore procedure:
#   1. Stop the application:      sudo systemctl stop pmas
#   2. Overwrite the database:    cp backups/pmas_2025-06-06T020000.db pmas.db
#   3. Restart the application:   sudo systemctl start pmas
#   4. Verify:                    curl -s http://localhost:8765/health | python3 -m json.tool

set -euo pipefail

DB_PATH="${1:-${PMAS_DB_PATH:-./pmas.db}}"
BACKUP_DIR="${2:-${PMAS_BACKUP_DIR:-./backups}}"
RETENTION_DAYS="${PMAS_BACKUP_RETENTION:-30}"

if [[ ! -f "$DB_PATH" ]]; then
  echo "ERROR: database not found at $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H%M%S")
DEST="${BACKUP_DIR}/pmas_${TIMESTAMP}.db"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting backup: $DB_PATH → $DEST"

sqlite3 "$DB_PATH" "VACUUM INTO '$DEST'"

SIZE=$(du -sh "$DEST" | cut -f1)
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup complete: $DEST ($SIZE)"

# Remove backups older than RETENTION_DAYS
PRUNED=$(find "$BACKUP_DIR" -maxdepth 1 -name 'pmas_*.db' \
         -mtime "+${RETENTION_DAYS}" -print -delete | wc -l)
if [[ $PRUNED -gt 0 ]]; then
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Pruned $PRUNED backup(s) older than ${RETENTION_DAYS} days"
fi
