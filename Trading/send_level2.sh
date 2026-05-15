#!/bin/bash
# Level 2 Signal Sender — XAUUSD + DXY + EUR/USD, GBP/USD, USD/JPY, USD/CHF
LOG_FILE="/root/.openclaw/workspace/Trading/signal_log.txt"
BOT_TOKEN="8714719077:AAG1k0QJh0_h5_ltWHvXQURD8Q6LbOTPlL0"
CHAT_ID="891202720"
API="https://api.telegram.org/bot${BOT_TOKEN}"

echo "--- $(date) ---" >> $LOG_FILE
echo "[LEVEL 2] Running..." >> $LOG_FILE

# Generate signal
TMPFILE=$(mktemp /tmp/level2_signal.XXXXXX)
/usr/bin/python3 /root/.openclaw/workspace/Trading/level2_signal.py > "$TMPFILE" 2>>"$LOG_FILE"
SIGNAL=$(cat "$TMPFILE")

if [ -z "$SIGNAL" ]; then
    echo "[LEVEL 2] ERROR: Empty signal" >> $LOG_FILE
    rm -f "$TMPFILE"
    exit 1
fi

# Send to Telegram
SEND_RESULT=$(curl -s -X POST "${API}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    --data-urlencode "text=${SIGNAL}" \
    -d parse_mode="Markdown" 2>&1)

# Extract message ID
NEW_MSG_ID=$(echo "$SEND_RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('result', {}).get('message_id', ''))
except:
    print('')
")

if [ -n "$NEW_MSG_ID" ]; then
    echo "[LEVEL 2] Sent: $NEW_MSG_ID" >> $LOG_FILE
    echo "$NEW_MSG_ID" > /root/.openclaw/workspace/Trading/last_signal_message.txt
else
    echo "[LEVEL 2] FAILED: $SEND_RESULT" >> $LOG_FILE
fi

rm -f "$TMPFILE"
