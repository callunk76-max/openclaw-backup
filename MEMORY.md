# Long Term Memory

- **Trading Bot Watchlist Command**: If Callunk sends a message like `/OpenPosisi [PAIR] [BUY/SELL/CLOSE]` (e.g. `/OpenPosisi AUDUSD BUY`), I must parse the command and execute `python3 /root/.openclaw/workspace/Trading/manage_positions.py [PAIR] [ACTION]` to update the active tracking list.