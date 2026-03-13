#!/usr/bin/env bash
#
# proxy-watchdog.sh — Keeps AdGuard VPN proxy alive
#
# Checks if the HTTP proxy at 127.0.0.1:2080 is responding.
# If not, restarts adguardvpn-cli. Run via cron every 2-5 minutes.
#
# Crontab entry:
#   */3 * * * * /home/v/Dev/ttt-expert-v1/expert-system/scripts/proxy-watchdog.sh >> /home/v/Dev/ttt-expert-v1/expert-system/logs/proxy-watchdog.log 2>&1
#

set -euo pipefail

PROXY_HOST="127.0.0.1"
PROXY_PORT="2080"
VPN_LOCATION="FI"
CONNECT_TIMEOUT=5

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Test proxy by connecting through it
if curl -s --proxy "http://${PROXY_HOST}:${PROXY_PORT}" \
     --connect-timeout "$CONNECT_TIMEOUT" \
     -o /dev/null \
     "https://api.ipify.org" 2>/dev/null; then
    # Proxy is alive — silent exit (uncomment next line for verbose logging)
    # log "Proxy OK"
    exit 0
fi

log "Proxy down — restarting AdGuard VPN..."

# Disconnect first (ignore errors if already disconnected)
adguardvpn-cli disconnect 2>/dev/null || true
sleep 2

# Reconnect
if adguardvpn-cli connect -l "$VPN_LOCATION" 2>&1; then
    sleep 3
    # Verify it came back
    if curl -s --proxy "http://${PROXY_HOST}:${PROXY_PORT}" \
         --connect-timeout "$CONNECT_TIMEOUT" \
         -o /dev/null \
         "https://api.ipify.org" 2>/dev/null; then
        log "Proxy restored"
    else
        log "WARNING: VPN connected but proxy still not responding"
    fi
else
    log "ERROR: adguardvpn-cli connect failed"
fi
