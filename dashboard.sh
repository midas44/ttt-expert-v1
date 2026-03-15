#!/usr/bin/env bash
# Regenerate and open the dashboard in Chromium
set -euo pipefail

DASHBOARD="expert-system/logs/dashboard.html"

python3 expert-system/scripts/generate-dashboard.py 2>/dev/null || true

if [[ -f "$DASHBOARD" ]]; then
    chromium-browser "$DASHBOARD" >/dev/null 2>&1 &
    echo "Dashboard opened in Chromium"
else
    echo "No dashboard found. Run at least one session first."
    exit 1
fi
