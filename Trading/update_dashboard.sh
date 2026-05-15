#!/bin/bash
# Update dashboard data + notify if breakout detected
LOG_FILE="/root/.openclaw/workspace/Trading/signal_log.txt"
BOT_TOKEN="8714719077:AAG1k0QJh0_h5_ltWHvXQURD8Q6LbOTPlL0"
CHAT_ID="891202720"
API="https://api.telegram.org/bot${BOT_TOKEN}"
LAST_MSG_FILE="/root/.openclaw/workspace/Trading/last_breakout_msg.txt"

echo "--- $(date) --- [DASHBOARD] Updating..." >> $LOG_FILE

# Seed H1 from CSV kalo file belum ada
H1_FILE="/root/.openclaw/workspace/Trading/dashboard/h1_candle.json"
if [ ! -f "$H1_FILE" ]; then
    /usr/bin/python3 /root/.openclaw/workspace/Trading/seed_h1.py >> "$LOG_FILE" 2>&1
fi

# Update dashboard data
TMPFILE=$(mktemp /tmp/dashboard_output.XXXXXX)
/usr/bin/python3 /root/.openclaw/workspace/Trading/volume_breakout.py --dashboard > "$TMPFILE" 2>>"$LOG_FILE"
EXIT_CODE=$?
SIGNAL=$(cat "$TMPFILE")

if [ -z "$SIGNAL" ]; then
    echo "[DASHBOARD] ERROR: Empty output" >> $LOG_FILE
    rm -f "$TMPFILE"
    exit 1
fi

# Copy dashboard files ke public directory
cp /root/.openclaw/workspace/Trading/dashboard/index.html /var/www/trading/index.html
cp /root/.openclaw/workspace/Trading/dashboard/data.json /var/www/trading/data.json
chown nginx:nginx /var/www/trading/*.html /var/www/trading/*.json 2>/dev/null

# Kirim ke Telegram cuma kalo ada breakout baru (exit code = 1)
if [ "$EXIT_CODE" -eq 1 ]; then
    # Hapus signal breakout sebelumnya kalo ada
    if [ -f "$LAST_MSG_FILE" ]; then
        OLD_MSG_ID=$(cat "$LAST_MSG_FILE")
        if [ -n "$OLD_MSG_ID" ]; then
            curl -s -X POST "${API}/deleteMessage" \
                -d chat_id="${CHAT_ID}" \
                -d message_id="${OLD_MSG_ID}" > /dev/null 2>&1
            echo "[DASHBOARD] Deleted breakout msg: $OLD_MSG_ID" >> $LOG_FILE
        fi
    fi

    # Kirim breakout alert
    SEND_RESULT=$(curl -s -X POST "${API}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        --data-urlencode "text=${SIGNAL}" \
        -d parse_mode="Markdown" 2>&1)

    MSG_ID=$(echo "$SEND_RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('result', {}).get('message_id', ''))
except:
    print('FAILED')
")

    if [ "$MSG_ID" != "FAILED" ]; then
        echo "$MSG_ID" > "$LAST_MSG_FILE"
        echo "[DASHBOARD] BREAKOUT ALERT sent: $MSG_ID" >> $LOG_FILE
    else
        echo "[DASHBOARD] BREAKOUT send failed: $SEND_RESULT" >> $LOG_FILE
    fi
fi

rm -f "$TMPFILE"
echo "[DASHBOARD] Updated OK (breakout exit: $EXIT_CODE)" >> $LOG_FILE
exit 0
