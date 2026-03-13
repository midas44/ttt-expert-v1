#!/usr/bin/env bash
#
# run-sessions.sh — Autonomous multi-session expert system runner
#
# Launches sequential Claude Code sessions that read/update the expert-system
# vault. Cross-session state lives in the vault + SQLite; this script just
# orchestrates the loop.
#
# Usage:
#   ./run-sessions.sh              # run until a stop condition is met
#   ./run-sessions.sh --sessions 3 # run exactly 3 sessions
#   ./run-sessions.sh --dry-run    # show prompts without executing
#

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/expert-system/config.yaml"
STATE_FILE=""   # set after config is parsed
LOG_DIR=""      # set after config is parsed

# ── CLI args ──────────────────────────────────────────────────────────────────
MAX_SESSIONS_OVERRIDE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sessions)
            MAX_SESSIONS_OVERRIDE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--sessions N] [--dry-run]" >&2
            exit 1
            ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { log "FATAL: $*" >&2; exit 1; }

setup_claude_md() {
    local target="$PROJECT_ROOT/CLAUDE.md"
    if [[ -e "$target" && ! -L "$target" ]]; then
        die "CLAUDE.md exists and is not a symlink — refusing to overwrite"
    fi
    ln -sf "CLAUDE+.md" "$target"
    log "Created CLAUDE.md -> CLAUDE+.md symlink"
}

cleanup_claude_md() {
    local target="$PROJECT_ROOT/CLAUDE.md"
    if [[ -L "$target" ]]; then
        rm "$target"
        # Only log if fd 1 is still open (may be called during exit)
        log "Removed CLAUDE.md symlink" 2>/dev/null || true
    fi
}

read_yaml() {
    # read_yaml <key> — extract a value from config.yaml via python3+yaml
    python3 -c "
import yaml, sys
with open('$CONFIG_FILE') as f:
    cfg = yaml.safe_load(f)
keys = '$1'.split('.')
v = cfg
for k in keys:
    v = v[k]
print(v)
" 2>/dev/null
}

# ── Preflight checks ─────────────────────────────────────────────────────────
preflight() {
    log "Preflight checks..."

    command -v claude >/dev/null 2>&1 || die "claude CLI not found"
    python3 -c "import yaml" 2>/dev/null || die "python3 pyyaml not installed"
    [[ -f "$CONFIG_FILE" ]] || die "Config not found: $CONFIG_FILE"

    local mode
    mode=$(read_yaml "autonomy.mode")
    [[ "$mode" == "full" ]] || die "autonomy.mode is '$mode', expected 'full'"

    # Check QMD MCP daemon is running
    if command -v qmd >/dev/null 2>&1; then
        if pgrep -f "qmd.*mcp" >/dev/null 2>&1; then
            log "QMD MCP daemon: running"
        else
            log "WARNING: QMD MCP daemon not running — starting it..."
            qmd mcp --http --daemon &
            sleep 3
            if pgrep -f "qmd.*mcp" >/dev/null 2>&1; then
                log "QMD MCP daemon: started"
            else
                log "WARNING: QMD MCP start failed — semantic search unavailable"
            fi
        fi
    else
        log "WARNING: qmd not found — semantic search unavailable"
    fi

    # Check playwright-vpn MCP server is registered (critical for UI exploration)
    if claude mcp get playwright-vpn >/dev/null 2>&1; then
        log "playwright-vpn MCP: registered"
    else
        log "WARNING: playwright-vpn MCP server not registered — UI exploration will be unavailable!"
        log "  Fix: see docs/playwright-mcp-fix.md for registration instructions"
    fi

    log "Preflight OK"
}

# ── Config parsing ────────────────────────────────────────────────────────────
parse_config() {
    MAX_SESSIONS=$(read_yaml "autonomy.max_sessions")
    CONSECUTIVE_FAILURE_LIMIT=$(read_yaml "autonomy.consecutive_failure_limit")
    LOG_DIR="$PROJECT_ROOT/$(read_yaml 'autonomy.log_dir')"
    STOP=$(read_yaml "autonomy.stop")
    MODEL=$(read_yaml "autonomy.model")
    EFFORT=$(read_yaml "autonomy.effort")
    DELAY_MINUTES=$(read_yaml "session.delay_minutes")
    DELAY_MINUTES_OFFHOURS=$(read_yaml "session.delay_minutes_offhours")
    OFFHOURS_UTC=$(read_yaml "session.offhours_utc")
    MAX_DURATION_MINUTES=$(read_yaml "session.max_duration_minutes")
    PHASE=$(read_yaml "phase.current")

    STATE_FILE="$LOG_DIR/runner-state.json"

    # CLI override
    if [[ -n "$MAX_SESSIONS_OVERRIDE" ]]; then
        MAX_SESSIONS="$MAX_SESSIONS_OVERRIDE"
    fi

    mkdir -p "$LOG_DIR"
}

get_current_delay() {
    local hour
    hour=$(date -u +%-H)  # current UTC hour (no leading zero)
    local start end
    start="${OFFHOURS_UTC%%:*}"        # "15" from "15:00-03:00"
    end="${OFFHOURS_UTC##*-}"          # "03:00"
    end="${end%%:*}"                   # "03"

    # Remove leading zeros for arithmetic
    start=$((10#$start))
    end=$((10#$end))
    hour=$((10#$hour))

    # Handle overnight range (e.g. 15-03 means hour>=15 OR hour<3)
    if (( start > end )); then
        if (( hour >= start || hour < end )); then
            echo "$DELAY_MINUTES_OFFHOURS"
            return
        fi
    else
        if (( hour >= start && hour < end )); then
            echo "$DELAY_MINUTES_OFFHOURS"
            return
        fi
    fi
    echo "$DELAY_MINUTES"
}

# ── State management ─────────────────────────────────────────────────────────
init_state() {
    if [[ -f "$STATE_FILE" ]]; then
        log "Resuming from existing state: $STATE_FILE"
    else
        log "Initializing new runner state"
        python3 -c "
import json
state = {
    'session_number': 0,
    'consecutive_failures': 0,
    'sessions': []
}
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"
    fi
}

get_state_field() {
    python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
print(state['$1'])
"
}

update_state() {
    # update_state <session_num> <exit_code> <duration_sec> <log_file>
    python3 -c "
import json, datetime
with open('$STATE_FILE') as f:
    state = json.load(f)

state['session_number'] = $1

if $2 != 0:
    state['consecutive_failures'] += 1
else:
    state['consecutive_failures'] = 0

state['sessions'].append({
    'session': $1,
    'timestamp': datetime.datetime.now().isoformat(),
    'exit_code': $2,
    'duration_sec': $3,
    'log_file': '$4'
})

with open('$STATE_FILE', 'w') as f:
    json.dump(state, f, indent=2)
"
}

# ── Prompt builders ───────────────────────────────────────────────────────────
build_prompt() {
    local session_num="$1"
    local phase="$2"

    if [[ "$session_num" -eq 1 ]]; then
        cat <<'PROMPT'
This is session 1 (bootstrap). autonomy.mode is "full" — do not wait for human approval.

Follow §16 (First Session Bootstrap) completely:
1. Read config.yaml
2. Read MISSION_DIRECTIVE.md
3. Create vault folder structure via mcp-obsidian
4. Initialize SQLite tables
5. Create _SESSION_BRIEFING.md, _INVESTIGATION_AGENDA.md, _KNOWLEDGE_COVERAGE.md, _INDEX.md
6. Set up QMD collection and embeddings
7. Clone repository
8. Verify MCP accessibility
9. Log Orientation plan to _SESSION_BRIEFING.md and begin Orientation immediately

After bootstrap, begin Orientation (§10 Sessions 1-3):
- Map repo structure
- Read existing docs
- Pull key Confluence pages
- Check Qase for existing tests
- Create architecture overview and module skeletons
- Run initial analysis tools
- Populate module_health table

At session end, follow §9.3 (update all underscore-prefixed files).
PROMPT
    else
        cat <<PROMPT
This is session ${session_num}. Phase: ${phase}. autonomy.mode is "full" — do not wait for human approval.

Follow §9 Session Protocol:
1. Read config.yaml
2. Check timing (log warning if needed, proceed regardless in full mode)
3. Read _SESSION_BRIEFING.md for prior session context
4. Read _INVESTIGATION_AGENDA.md
5. Read MISSION_DIRECTIVE.md — check for updates
6. Query SQLite for recent activity
7. QMD search for recent context
8. Pick top 2-3 items from _INVESTIGATION_AGENDA.md by priority

Execute the INVESTIGATE → ANALYZE → SYNTHESIZE → STORE → CONNECT cycle for each item.

$(if (( session_num % 5 == 0 )); then echo "This is session ${session_num} (multiple of 5) — also run maintenance per §9.4: compress old investigations, detect stale notes, audit cross-references, clean SQLite, refine agenda."; fi)

At session end, follow §9.3 strictly:
- Update _SESSION_BRIEFING.md (timestamp, findings, state, next steps)
- Update _INVESTIGATION_AGENDA.md (completed, new, re-prioritized)
- Update _KNOWLEDGE_COVERAGE.md (coverage changes)
- Update _INDEX.md if new notes created
- Run qmd embed if significant notes added
PROMPT
    fi
}

# ── Stop condition checks ────────────────────────────────────────────────────
check_stop_conditions() {
    local session_num="$1"

    # 1. Stop flag in config
    if [[ "$STOP" == "True" ]]; then
        log "autonomy.stop is true in config.yaml"
        return 1
    fi

    # 2. Max sessions
    if [[ "$MAX_SESSIONS" -gt 0 && "$session_num" -gt "$MAX_SESSIONS" ]]; then
        log "Max sessions reached ($MAX_SESSIONS)"
        return 1
    fi

    # 3. Consecutive failures
    local failures
    failures=$(get_state_field "consecutive_failures")
    if [[ "$failures" -ge "$CONSECUTIVE_FAILURE_LIMIT" ]]; then
        log "Consecutive failure limit reached ($failures >= $CONSECUTIVE_FAILURE_LIMIT)"
        return 1
    fi

    return 0
}

# ── Vault versioning ─────────────────────────────────────────────────────────
commit_vault() {
    local session_num="$1"
    local exit_code="$2"
    local duration="$3"
    local vault_dir="$PROJECT_ROOT/expert-system/vault"

    if [[ -d "$vault_dir/.git" ]] || \
       git -C "$vault_dir" init --quiet 2>/dev/null; then
        git -C "$vault_dir" add -A 2>/dev/null
        git -C "$vault_dir" \
            -c user.name="Expert System" -c user.email="expert@local" \
            commit -m "Session $session_num (exit $exit_code, ${duration}s)" \
            --allow-empty 2>/dev/null || true
    fi
}

# ── Completion notification ──────────────────────────────────────────────────
notify_completion() {
    local reason="$1"
    local total_sessions
    total_sessions=$(get_state_field 'session_number')

    log "━━━ Runner finished ━━━"
    log "Reason: $reason"
    log "Total sessions: $total_sessions"
    log "State: $STATE_FILE"

    # Desktop notification (non-fatal if unavailable)
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u normal "Expert System Runner" \
            "Finished after $total_sessions sessions. Reason: $reason" 2>/dev/null || true
    fi
}

# ── Main loop ─────────────────────────────────────────────────────────────────
main() {
    setup_claude_md
    trap cleanup_claude_md EXIT

    preflight
    parse_config
    init_state

    # Persist runner log to file
    exec > >(tee -a "$LOG_DIR/runner.log") 2>&1

    local session_num
    session_num=$(( $(get_state_field "session_number") + 1 ))

    log "Starting from session $session_num (max: $MAX_SESSIONS)"
    log "Model: $MODEL, effort: $EFFORT"
    log "Phase: $PHASE"
    log "Log dir: $LOG_DIR"
    log "Stop flag: $STOP"
    log "Session timeout: $((MAX_DURATION_MINUTES + 30)) minutes"
    log "Session delay: ${DELAY_MINUTES}min (working) / ${DELAY_MINUTES_OFFHOURS}min (off-hours: ${OFFHOURS_UTC} UTC)"

    local stop_reason="unknown"

    while check_stop_conditions "$session_num"; do
        # Re-read config each iteration (phase may have changed)
        parse_config

        local prompt
        prompt=$(build_prompt "$session_num" "$PHASE")

        local log_file="$LOG_DIR/session-$(printf '%03d' "$session_num")-$(date '+%Y%m%d-%H%M%S').json"
        local stderr_file="${log_file%.json}.stderr"

        log "━━━ Session $session_num ━━━"

        if $DRY_RUN; then
            log "[DRY RUN] Would execute session $session_num"
            log "[DRY RUN] Prompt:"
            echo "---"
            echo "$prompt"
            echo "---"
            log "[DRY RUN] Log file: $log_file"
            log "[DRY RUN] Command: HTTP_PROXY=http://127.0.0.1:2080 HTTPS_PROXY=http://127.0.0.1:2080 timeout $((( MAX_DURATION_MINUTES + 30 ) * 60))s claude -p --output-format json --model $MODEL --effort $EFFORT --dangerously-skip-permissions"
            session_num=$((session_num + 1))
            continue
        fi

        local start_time
        start_time=$(date +%s)

        local exit_code=0
        local timeout_seconds=$(( (MAX_DURATION_MINUTES + 30) * 60 ))

        HTTP_PROXY=http://127.0.0.1:2080 \
        HTTPS_PROXY=http://127.0.0.1:2080 \
        timeout --signal=TERM --kill-after=60 "$timeout_seconds" \
            claude -p \
                --output-format json \
                --model "$MODEL" \
                --effort "$EFFORT" \
                --dangerously-skip-permissions \
                "$prompt" \
                < /dev/null > "$log_file" 2>"$stderr_file" || exit_code=$?

        local end_time
        end_time=$(date +%s)
        local duration=$(( end_time - start_time ))

        if [[ "$exit_code" -eq 124 ]]; then
            log "Session $session_num TIMED OUT after $((timeout_seconds / 60)) minutes"
        fi

        update_state "$session_num" "$exit_code" "$duration" "$log_file"
        commit_vault "$session_num" "$exit_code" "$duration"

        if [[ "$exit_code" -eq 0 ]]; then
            log "Session $session_num completed (${duration}s)"
        elif [[ "$exit_code" -ne 124 ]]; then
            log "Session $session_num FAILED with exit code $exit_code (${duration}s)"
        fi

        session_num=$((session_num + 1))

        # Inter-session delay (skip if this was the last session)
        if check_stop_conditions "$session_num" 2>/dev/null; then
            local current_delay
            current_delay=$(get_current_delay)
            local delay_mode="working hours"
            [[ "$current_delay" -eq "$DELAY_MINUTES_OFFHOURS" ]] && delay_mode="off-hours"
            log "Waiting ${current_delay} minutes before next session ($(date -u '+%H:%M') UTC, ${delay_mode})"
            sleep $(( current_delay * 60 ))
        fi
    done

    # Determine stop reason
    if [[ "$STOP" == "True" ]]; then
        stop_reason="autonomy.stop set to true"
    elif [[ "$MAX_SESSIONS" -gt 0 && "$session_num" -gt "$MAX_SESSIONS" ]]; then
        stop_reason="max sessions reached ($MAX_SESSIONS)"
    elif [[ "$(get_state_field 'consecutive_failures')" -ge "$CONSECUTIVE_FAILURE_LIMIT" ]]; then
        stop_reason="consecutive failure limit ($CONSECUTIVE_FAILURE_LIMIT)"
    else
        stop_reason="all sessions completed"
    fi

    notify_completion "$stop_reason"
}

main
