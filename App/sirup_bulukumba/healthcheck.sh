#!/bin/bash
# Healthcheck for sirup_bulukumba - uses systemd now
if systemctl is-active --quiet sirup-bulukumba; then
    exit 0
fi

# If systemd failed, try restart
systemctl restart sirup-bulukumba
echo "[$(date)] sirup_bulukumba restarted via systemd" >> /root/.openclaw/workspace/App/sirup_bulukumba/restart_log.txt
