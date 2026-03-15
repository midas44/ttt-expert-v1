#!/usr/bin/env bash
# Start the expert system runner in a tmux session
set -euo pipefail

SESSION="expert"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Runner already running in tmux session '$SESSION'"
    echo "  Attach: tmux attach -t $SESSION"
    echo "  Stop:   ./stop.sh"
    exit 1
fi

tmux new-session -d -s "$SESSION" ./expert-system/scripts/run-sessions.sh
echo "Runner started in tmux session '$SESSION'"
echo "  Attach:    tmux attach -t $SESSION"
echo "  Stop:      ./stop.sh"
echo "  Dashboard: ./dashboard.sh"
