#!/bin/bash
cd /opt/apps/vehicle_job_tracker || exit 1

BACKUP_DIR="/opt/apps/vehicle_job_tracker/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="$BACKUP_DIR/backup_$TIMESTAMP.sql"

docker compose exec -T db pg_dump -U vjt_user vehicle_job_tracker > "$FILENAME"

# Keep only the last 14 daily backups, delete anything older
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +14 -delete