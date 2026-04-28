#!/bin/bash
# Auto-restart for sirup_bulukumba Flask app
APP_DIR="/root/.openclaw/workspace/App/sirup_bulukumba"
PID_FILE="/tmp/sirup_bulukumba.pid"

if curl -sf http://127.0.0.1:5005/ > /dev/null 2>&1; then
    exit 0
fi

# App is down, restart it
cd "$APP_DIR"
nohup python3 app.py > app.log 2>&1 &
echo $! > "$PID_FILE"
echo "[$(date)] sirup_bulukumba restarted (was down)" >> restart_log.txt
