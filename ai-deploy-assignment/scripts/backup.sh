#!/bin/bash
# Backs up the Postgres database to a timestamped .sql file.
# Run manually, or schedule with cron, e.g.:
#   0 2 * * * /path/to/backup.sh >> /var/log/db_backup.log 2>&1

set -euo pipefail

cd "$(dirname "$0")/.."

# Load env vars
set -a
source .env
set +a

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"

echo "[$(date)] Backup written to $BACKUP_FILE"

# Compress it
gzip "$BACKUP_FILE"
echo "[$(date)] Compressed to ${BACKUP_FILE}.gz"

# Remove backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup complete. Old backups (>$RETENTION_DAYS days) pruned."
