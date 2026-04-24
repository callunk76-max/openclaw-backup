#!/bin/bash
# Backup script for OpenClaw workspace to GitHub
WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/github_backup"
SSH_KEY="/root/.ssh/id_ed25519_openclaw"

# Sync current workspace to backup folder
rsync -av --exclude='github_backup' --exclude='.git' --exclude='__pycache__' "$WORKSPACE/" "$BACKUP_DIR/"

# Push to GitHub
cd "$BACKUP_DIR"
GIT_SSH_COMMAND="ssh -i $SSH_KEY" git add .
GIT_SSH_COMMAND="ssh -i $SSH_KEY" git commit -m "Daily Backup from Cuy - $(date '+%Y-%m-%d %H:%M')"
if GIT_SSH_COMMAND="ssh -i $SSH_KEY" git push origin main; then
    /root/.nvm/versions/node/v22.22.1/bin/openclaw message send --channel telegram --target "891202720" --message "sep, backup done! 👑🚀"
fi
