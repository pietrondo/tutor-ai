#!/bin/bash

# Smart Backup Script for Tutor-AI
# Excludes node_modules and only backs up essential files

BACKUP_DIR="tutor-ai-backup-$(date +%Y%m%d-%H%M%S)"
PROJECT_ROOT="$(pwd)"

echo "Creating smart backup in: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy essential project files
echo "Copying project files..."
cp -r docker-compose*.yml "$BACKUP_DIR/" 2>/dev/null || true
cp -r backend "$BACKUP_DIR/"
cp -r frontend "$BACKUP_DIR/"
cp -r data "$BACKUP_DIR/"
cp *.md "$BACKUP_DIR/" 2>/dev/null || true
cp .gitignore "$BACKUP_DIR/" 2>/dev/null || true

# Remove node_modules from backup
echo "Removing node_modules from backup..."
rm -rf "$BACKUP_DIR/frontend/node_modules"
rm -rf "$BACKUP_DIR/backend/venv" 2>/dev/null || true
rm -rf "$BACKUP_DIR/backend/env" 2>/dev/null || true
rm -rf "$BACKUP_DIR/backend/__pycache__" 2>/dev/null || true

# Create a backup info file
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Backup type: Smart backup (node_modules excluded)
Original project size: $(du -sh "$PROJECT_ROOT" | cut -f1)
Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)

Contents:
- Backend source code (Python)
- Frontend source code (TypeScript/Next.js)
- Docker configuration
- Data files and courses
- Documentation

Excluded:
- node_modules (reinstallable)
- Python cache files
- Build artifacts
EOF

echo "Backup completed!"
echo "Backup location: $BACKUP_DIR"
echo "Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore:"
echo "1. cd $BACKUP_DIR"
echo "2. docker-compose up -d"
echo "3. cd frontend && npm install"
echo "4. cd ../backend && pip install -r requirements.txt"