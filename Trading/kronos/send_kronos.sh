#!/bin/bash
# Kronos Signal Sender via Telegram Bot API
LOG_FILE="/root/.openclaw/workspace/Trading/kronos/kronos_cron.log"
SIGNAL_FILE="/root/.openclaw/workspace/Trading/kronos/last_kronos_msg.txt"
BOT_TOKEN="8714719077:AAG1k0QJh0_h5_ltWHvXQURD8Q6LbOTPlL0"
CHAT_ID="891202720"
API="https://api.telegram.org/bot${BOT_TOKEN}"

echo "--- $(date) ---" >> $LOG_FILE

# Run pipeline
OUTPUT=$(/usr/bin/python3 -u /root/.openclaw/workspace/Trading/kronos/pipeline.py 2>&1)
PIPELINE_EXIT=$?

# Log output
echo "$OUTPUT" >> $LOG_FILE 2>&1

if [ $PIPELINE_EXIT -ne 0 ]; then
    echo "PIPELINE FAILED: exit $PIPELINE_EXIT" >> $LOG_FILE
    exit 1
fi

# Extract signal summary (last line after === separator)
SIGNAL=$(echo "$OUTPUT" | grep -A100 "^📊" | tail -n +1 | head -20)

# Read predictions/signals and format message
MSG=$(/usr/bin/python3 -c "
import sys, os
sys.path.insert(0, '/root/.openclaw/workspace/Trading/kronos')
from signal_gen import get_signal_summary
print(get_signal_summary())
" 2>>$LOG_FILE)

echo "Signal: $MSG" >> $LOG_FILE

# Send via Telegram Bot API
SEND_RESULT=$(curl -s -X POST "${API}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    --data-urlencode "text=${MSG}" \
    -d parse_mode="Markdown" 2>&1)

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
    
    # Delete previous signal
    if [ -f "$SIGNAL_FILE" ]; then
        OLD_MSG_ID=$(cat "$SIGNAL_FILE")
        if [ -n "$OLD_MSG_ID" ] && [ "$OLD_MSG_ID" != "$NEW_MSG_ID" ]; then
            curl -s -X POST "${API}/deleteMessage" \
                -d chat_id="${CHAT_ID}" \
                -d message_id="${OLD_MSG_ID}" > /dev/null 2>&1
            echo "Deleted old: $OLD_MSG_ID" >> $LOG_FILE
        fi
    fi
    
    echo "$NEW_MSG_ID" > "$SIGNAL_FILE"
else
    echo "SEND FAIL: $(echo $SEND_RESULT | head -c 200)" >> $LOG_FILE
fi
