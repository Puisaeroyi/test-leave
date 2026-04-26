#!/bin/bash

BACKUP_DIR="/home/tadmin/backups/media"
VOLUME_NAME="leave_management_media_data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/media_$TIMESTAMP.tar.gz"
LOG_FILE="$BACKUP_DIR/backup.log"

echo "[$TIMESTAMP] Starting backup..." >> "$LOG_FILE"

docker run --rm \
  -v "$VOLUME_NAME":/data:ro \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/media_$TIMESTAMP.tar.gz" -C /data .

if [ $? -eq 0 ]; then
  echo "[$TIMESTAMP] Backup successful: $BACKUP_FILE" >> "$LOG_FILE"
else
  echo "[$TIMESTAMP] Backup FAILED" >> "$LOG_FILE"
  exit 1
fi
