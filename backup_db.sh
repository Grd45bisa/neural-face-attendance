#!/bin/bash

echo "========================================"
echo "  MongoDB Backup Script"
echo "========================================"
echo ""

# Create backups folder if not exists
mkdir -p backups

# Get current date
BACKUP_DATE=$(date +%Y%m%d)

echo "Backing up MongoDB database: tugas_production"
echo "Backup date: $BACKUP_DATE"
echo ""

# Backup MongoDB
mongodump --db tugas_production --out backups/backup_$BACKUP_DATE

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Backup failed!"
    echo "Make sure MongoDB is running and mongodump is in PATH"
    exit 1
fi

echo ""
echo "Backup completed successfully!"
echo "Location: backups/backup_$BACKUP_DATE"
echo ""

# Keep only last 7 backups
echo "Cleaning old backups (keeping last 7)..."
find backups/ -type d -name "backup_*" -mtime +7 -exec rm -rf {} + 2>/dev/null

echo ""
echo "Done!"
