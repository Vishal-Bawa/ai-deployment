#!/bin/bash
# Restores the Postgres database from a backup file.
# Usage: ./restore.sh ./backups/backup_20260701_020000.sql.gz

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <path-to-backup-file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

set -a
source .env
set +a

echo "[$(date)] Restoring from $BACKUP_FILE ..."
echo "WARNING: This will overwrite the current database. Press Ctrl+C to cancel."
sleep 5

gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "[$(date)] Restore complete."
