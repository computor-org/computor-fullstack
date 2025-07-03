#!/bin/bash

echo "$BACKUP_CRON /bin/bash /backup_run.sh" | crontab -

echo "[INFO] Starte crond..."
crond -f -L /dev/stdout