#!/bin/bash
# OSS Polygon Editor - Health Check Script
# Run via cron every minute or as needed

APP_DIR="/root/.openclaw/workspace/App/os"
PORT=5008
LOG="$APP_DIR/restart_log.txt"
HEALTH_FILE="$APP_DIR/health.txt"

timestamp() { echo "$(date '+%Y-%m-%d %H:%M:%S')"; }

# 1. Check if gunicorn is listening on port
if ! lsof -iTCP:$PORT -sTCP:LISTEN > /dev/null 2>&1; then
    echo "$(timestamp) ❌ gunicorn not listening on port $PORT. Restarting..." >> "$LOG"

    # Kill any stale processes
    pkill -f "gunicorn.*5008" 2>/dev/null
    sleep 2

    cd "$APP_DIR"
    nohup gunicorn -w 2 -b 127.0.0.1:$PORT --timeout 120 \
        --access-logfile - --error-logfile - \
        app:app </dev/null > /dev/null 2>&1 &

    sleep 3

    if lsof -iTCP:$PORT -sTCP:LISTEN > /dev/null 2>&1; then
        echo "$(timestamp) ✅ Restart successful" >> "$LOG"
    else
        echo "$(timestamp) ❌ Restart FAILED" >> "$LOG"
    fi
fi

# 2. Check health endpoint
if lsof -iTCP:$PORT -sTCP:LISTEN > /dev/null 2>&1; then
    STATUS=$(curl -sf http://127.0.0.1:$PORT/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
    if [ "$STATUS" != "ok" ]; then
        echo "$(timestamp) ⚠️ Health check failed (status=$STATUS). Restarting..." >> "$LOG"
        pkill -f "gunicorn.*5008" 2>/dev/null
        sleep 2
        cd "$APP_DIR"
        nohup gunicorn -w 2 -b 127.0.0.1:$PORT --timeout 120 \
            --access-logfile - --error-logfile - \
            app:app </dev/null > /dev/null 2>&1 &
    fi
fi
