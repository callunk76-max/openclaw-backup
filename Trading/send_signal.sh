#!/bin/bash
# Run the trading signal analysis and log output
LOG_FILE="/root/.openclaw/workspace/Trading/signal_log.txt"
echo "--- Running Signal at $(date) ---" >> $LOG_FILE
SIGNAL=$(/usr/bin/python3 /root/.openclaw/workspace/Trading/trading_signal.py 2>&1)
echo "Signal Result: $SIGNAL" >> $LOG_FILE

# Send the signal via OpenClaw CLI
/root/.nvm/versions/node/v22.22.1/bin/openclaw message send --channel telegram --target "891202720" --message "$SIGNAL" >> $LOG_FILE 2>&1
echo "Message sent status: $?" >> $LOG_FILE
