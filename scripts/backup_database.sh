#!/bin/bash

BACKUP_DIR="/home/tadmin/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/backup.log"

ENV_FILE="/home/tadmin/leave_management/.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -E '^POSTGRES_(DB|USER|PASSWORD)' "$ENV_FILE" | xargs)
fi

echo "[$TIMESTAMP] Starting database backup..." >> "$LOG_FILE"

docker exec leave_db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "[$TIMESTAMP] Backup successful: $BACKUP_FILE" >> "$LOG_FILE"
else
  echo "[$TIMESTAMP] Backup FAILED" >> "$LOG_FILE"
  rm -f "$BACKUP_FILE"
  exit 1
fi
