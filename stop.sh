#!/usr/bin/env bash
# Gracefully stop the runner after the current session finishes
set -euo pipefail

CONFIG="expert-system/config.yaml"

python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['autonomy']['stop'] = True
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
"

echo "Set autonomy.stop: true in config.yaml"
echo "Runner will stop after the current session finishes."
echo "To resume later: set autonomy.stop: false, then ./start.sh"
