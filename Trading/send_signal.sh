#!/bin/bash
# Trading signal via direct Telegram Bot API (no OpenClaw lock issues)
LOG_FILE="/root/.openclaw/workspace/Trading/signal_log.txt"
SIGNAL_FILE="/root/.openclaw/workspace/Trading/last_signal_message.txt"
BOT_TOKEN="8714719077:AAG1k0QJh0_h5_ltWHvXQURD8Q6LbOTPlL0"
CHAT_ID="891202720"
API="https://api.telegram.org/bot${BOT_TOKEN}"

echo "--- $(date) ---" >> $LOG_FILE

# Generate signal, save to temp file to avoid shell escaping issues
TMPFILE=$(mktemp /tmp/trading_signal.XXXXXX)
/usr/bin/python3 /root/.openclaw/workspace/Trading/trading_signal.py > "$TMPFILE" 2>>"$LOG_FILE"
SIGNAL=$(cat "$TMPFILE")

# STEP 1: Send via Telegram Bot API (use @file for raw content)
SEND_RESULT=$(curl -s -X POST "${API}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    --data-urlencode "text=${SIGNAL}" \
    -d parse_mode="Markdown" 2>&1)

# Extract new message ID
NEW_MSG_ID=$(echo "$SEND_RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('result', {}).get('message_id', ''))
except:
    print('')
")

if [ -n "$NEW_MSG_ID" ]; then
    echo "Sent: $NEW_MSG_ID" >> $LOG_FILE
    
    # STEP 2: Delete previous signal
    if [ -f "$SIGNAL_FILE" ]; then
        OLD_MSG_ID=$(cat "$SIGNAL_FILE")
        if [ -n "$OLD_MSG_ID" ] && [ "$OLD_MSG_ID" != "$NEW_MSG_ID" ]; then
            curl -s -X POST "${API}/deleteMessage" \
                -d chat_id="${CHAT_ID}" \
                -d message_id="${OLD_MSG_ID}" > /dev/null 2>&1
            echo "Deleted: $OLD_MSG_ID" >> $LOG_FILE
        fi
    fi
    
    echo "$NEW_MSG_ID" > "$SIGNAL_FILE"
else
    echo "FAIL: $(echo $SEND_RESULT | head -c 200)" >> $LOG_FILE
fi

rm -f "$TMPFILE"