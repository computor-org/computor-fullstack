#!/bin/bash

set -e

export PGPASSWORD=${POSTGRES_PASSWORD}

TIMESTAMP=$(date +%F_%H-%M-%S)
WORKDIR="/tmp/backup_$TIMESTAMP"
mkdir -p "$WORKDIR"

DUMP_FILE="$WORKDIR/db_dump.sql"
ZIP_FILE="$BACKUP_PATH/backup_$TIMESTAMP.zip"

echo "[INFO] Starting backup at $(date)"

pg_dump -h "$POSTGRES_HOST" -p 5437 -U "$POSTGRES_USER" "$POSTGRES_DB" > "$DUMP_FILE"
if [ $? -ne 0 ]; then
    echo "[ERROR] pg_dump failed!"
    exit 1
fi
echo "[INFO] Database dump created: $DUMP_FILE"

if ! grep -q "^-- PostgreSQL database dump" "$DUMP_FILE"; then
    echo "[ERROR] Dump validation failed"
    exit 1
fi
echo "[INFO] Dump validation successful"

# IFS=',' read -ra FOLDERS <<< "$FOLDERS_TO_ZIP"
# zip -r "$ZIP_FILE" "${FOLDERS[@]}"
# echo "[INFO] Folders zipped to: $ZIP_FILE"

IFS=',' read -ra FOLDERS <<< "$FOLDERS_TO_ZIP"
for folder in "${FOLDERS[@]}"; do
    if [ -d "$folder" ]; then
        cp -r "$folder" "$WORKDIR/"
    else
        echo "[WARNING] Folder not found: $folder"
    fi
done

cd "$WORKDIR"
zip -r "$ZIP_FILE" ./*
cd -

echo "[INFO] Backup archive created: $ZIP_FILE"

rm -rf "$WORKDIR"

echo "[INFO] Backup completed at $(date)"
