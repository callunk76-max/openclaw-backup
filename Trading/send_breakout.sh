#!/bin/bash
# Volume Breakout Scanner — H1 | Auto-send to Telegram
# Otomatis hapus signal sebelumnya sebelum kirim yg baru

LOG_FILE="/root/.openclaw/workspace/Trading/signal_log.txt"
BOT_TOKEN="8714719077:AAG1k0QJh0_h5_ltWHvXQURD8Q6LbOTPlL0"
CHAT_ID="891202720"
API="https://api.telegram.org/bot${BOT_TOKEN}"
LAST_MSG_FILE="/root/.openclaw/workspace/Trading/last_breakout_msg.txt"

echo "--- $(date) --- [BREAKOUT] Starting scan..." >> $LOG_FILE

# ── HAPUS SIGNAL SEBELUMNYA ──
if [ -f "$LAST_MSG_FILE" ]; then
    OLD_MSG_ID=$(cat "$LAST_MSG_FILE")
    if [ -n "$OLD_MSG_ID" ]; then
        DELETE_RESULT=$(curl -s -X POST "${API}/deleteMessage" \
            -d chat_id="${CHAT_ID}" \
            -d message_id="${OLD_MSG_ID}" 2>&1)
        echo "[BREAKOUT] Deleted: $OLD_MSG_ID ($DELETE_RESULT)" >> $LOG_FILE
    fi
fi

# ── RUN SCAN ──
TMPFILE=$(mktemp /tmp/breakout_signal.XXXXXX)
/usr/bin/python3 /root/.openclaw/workspace/Trading/volume_breakout.py > "$TMPFILE" 2>>"$LOG_FILE"
EXIT_CODE=$?
SIGNAL=$(cat "$TMPFILE")

if [ -z "$SIGNAL" ]; then
    echo "[BREAKOUT] ERROR: Empty signal" >> $LOG_FILE
    rm -f "$TMPFILE"
    exit 1
fi

# ── KIRIM SIGNAL BARU ──
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
    echo "[BREAKOUT] Sent: $MSG_ID (breakouts: $EXIT_CODE)" >> $LOG_FILE
else
    echo "[BREAKOUT] Send failed: $SEND_RESULT" >> $LOG_FILE
fi

rm -f "$TMPFILE"
exit 0
