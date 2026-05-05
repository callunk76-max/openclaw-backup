# Long Term Memory

- **Trading Bot Watchlist Command**: If Callunk sends a message like `/OpenPosisi [PAIR] [BUY/SELL/CLOSE]` (e.g. `/OpenPosisi AUDUSD BUY`), I must parse the command and execute `python3 /root/.openclaw/workspace/Trading/manage_positions.py [PAIR] [ACTION]` to update the active tracking list.

## SIRUP Bulukumba App

**CRITICAL: App runs on GUNICORN, not Flask dev server!**
- Port: 5005, served via nginx at callunk.my.id/
- Gunicorn command: `cd /root/.openclaw/workspace/App/sirup_bulukumba && gunicorn -w 4 -b 127.0.0.1:5005 --timeout 120 --access-logfile - --error-logfile - app:app`
- Template: `templates/index.html`
- After editing templates, MUST restart gunicorn: `kill $(lsof -ti:5005) && sleep 2 && cd /root/.openclaw/workspace/App/sirup_bulukumba && gunicorn -w 4 -b 127.0.0.1:5005 --timeout 120 --access-logfile - --error-logfile - app:app </dev/null > /dev/null 2>&1 &`
- NO systemd service active (healthcheck.sh exists but unused)