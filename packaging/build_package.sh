#!/usr/bin/env bash
# Build the Linux install package from a standalone binary.
#
#   packaging/build_package.sh PATH_TO_BINARY [OUTPUT_DIR]
#
# The result is OUTPUT_DIR/pmas-linux-x64-package.tar.gz (default OUTPUT_DIR: dist).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BINARY="${1:?Give the path of the binary}"
OUT="${2:-$ROOT/dist}"
[[ -f "$BINARY" ]] || { echo "Binary not found: $BINARY" >&2; exit 1; }

NAME="pmas-linux-x64-package"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$NAME" "$OUT"

install -m 0755 "$BINARY" "$STAGE/$NAME/pmas"
install -m 0755 "$ROOT/packaging/install.sh" "$STAGE/$NAME/install.sh"
install -m 0755 "$ROOT/backup_pmas.sh" "$STAGE/$NAME/backup_pmas.sh"
for f in pmas.service pmas-backup.service pmas-backup.timer pmas.env.example; do
  install -m 0644 "$ROOT/packaging/$f" "$STAGE/$NAME/$f"
done
install -m 0644 "$ROOT/docs/OPERATIONS.md" "$STAGE/$NAME/OPERATIONS.md"

tar -C "$STAGE" -czf "$OUT/$NAME.tar.gz" "$NAME"
echo "$OUT/$NAME.tar.gz"
