# Autonomy Mode Guide — Running the Expert System Unattended

> **Purpose:** Step-by-step guide for preparing, launching, monitoring, and managing the expert system in fully autonomous mode — where sessions run unattended via a shell loop.
>
> **Prerequisite:** The base expert system must already be set up per `docs/human-guide.md`. This guide covers only the autonomy-specific additions.
>
> **Billing:** This system is designed for the Claude MAX plan subscription. The inter-session delay is tuned to consume ~60% of the daily 5h token budget, leaving headroom for interactive use.

---

## 1. How It Works

In autonomous mode, a shell script (`expert-system/scripts/run-sessions.sh`) launches sequential `claude -p` sessions. Each session:

1. Reads `CLAUDE.md` + `config.yaml` (autonomy.mode = "full")
2. Reads vault state (`_SESSION_BRIEFING.md`, `_INVESTIGATION_AGENDA.md`, etc.)
3. Picks top investigation items, executes them without waiting for human approval
4. Updates vault notes, SQLite, and coverage tracking
5. Exits

The script captures exit codes, enforces stop conditions, and maintains a state file (`runner-state.json`) across sessions. Cross-session memory lives entirely in the vault and SQLite — each `claude -p` invocation is stateless.

```
┌─────────────────────────────────────────────────────┐
│              run-sessions.sh (loop)                 │
│                                                     │
│  ┌──────────┐   ┌──────────┐        ┌──────────┐  │
│  │Session 1 │──▶│Session 2 │──...──▶│Session N │  │
│  │bootstrap │   │ regular  │        │ regular  │  │
│  └────┬─────┘   └────┬─────┘        └────┬─────┘  │
│       │              │                    │        │
│       ▼              ▼                    ▼        │
│  ┌─────────────────────────────────────────────┐   │
│  │       Vault + SQLite (shared state)         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 2. Preparation Checklist

### 2.1 Verify Base Setup

Everything from `docs/human-guide.md` must be working:

```bash
# All must pass
claude --version
python3 -c "import yaml; print('pyyaml OK')"
qmd status
claude mcp list | head -5

# Verify playwright-vpn MCP (critical for UI exploration)
claude mcp get playwright-vpn
# If missing, see docs/playwright-mcp-fix.md
```

### 2.2 Review config.yaml

The `autonomy` section in `expert-system/config.yaml`:

```yaml
autonomy:
  mode: "full"                       # "hybrid" or "full"
  max_sessions: 30                   # Stop after N sessions (0 = unlimited)
  consecutive_failure_limit: 3       # Abort after N consecutive failures
  auto_phase_transition: false       # Auto-switch to Phase B when coverage target met
  log_dir: "expert-system/logs"      # Session log directory
  stop_file: "expert-system/.stop"   # Touch to gracefully stop the loop
  model: "opus"                      # Model for claude -p
  effort: "max"                      # Effort level
  allow_api_mutations: false         # If false, only GET/SELECT in autonomous mode
```

**Key decisions before first run:**

| Setting | Default | Consider changing if... |
|---------|---------|------------------------|
| `max_sessions` | 30 | You want fewer/more sessions total |
| `allow_api_mutations` | false | You trust autonomous POST/PATCH/DELETE on test envs |
| `auto_phase_transition` | false | You want Phase B to start automatically when coverage is met |
| `model` | opus | You want to use a different model |
| `session.delay_minutes` | 420 | See §2.3 for tuning guidance |

### 2.3 Session Delay and Token Budget

The MAX plan has a 5h daily token budget. Empirically, **140 min of wall-clock Claude runtime consumes 100% of the 5h budget** (burn rate ~2.14x). The inter-session delay controls how much of the daily budget the runner consumes.

The default `delay_minutes: 420` (7 hours) targets ~60% daily consumption, assuming 25-30 min average session duration.

#### Delay Reference Table (T = 25 min avg session)

| Delay | Sessions/day | Active time/day | Tokens consumed/day | % of 5h budget | Days to finish 30 sessions |
|---|---|---|---|---|---|
| 240 min (4h) | 5.4 | 2h16m | 4h52m | **97%** | 5.5 |
| 300 min (5h) | 4.4 | 1h51m | 3h57m | 79% | 6.8 |
| 360 min (6h) | 3.7 | 1h34m | 3h20m | 67% | 8.0 |
| **420 min (7h)** | **3.2** | **1h21m** | **2h53m** | **58%** | **9.3** |
| 480 min (8h) | 2.9 | 1h11m | 2h33m | 51% | 10.5 |
| 540 min (9h) | 2.5 | 1h04m | 2h16m | 45% | 11.8 |

#### Impact of Session Duration (delay = 420 min)

| Avg session | Sessions/day | Active time/day | Tokens/day | % of 5h | Days for 30 |
|---|---|---|---|---|---|
| 15 min | 3.3 | 50m | 1h47m | 36% | 9.1 |
| 20 min | 3.3 | 65m | 2h19m | 47% | 9.2 |
| **25 min** | **3.2** | **81m** | **2h53m** | **58%** | **9.3** |
| 30 min | 3.2 | 96m | 3h26m | 69% | 9.4 |
| 45 min | 3.1 | 139m | 4h58m | 99% | 9.7 |

#### Projected 30-Session Timeline (T = 25 min, delay = 420 min)

Each session consumes ~54 min of token budget (25 min × 2.14 burn rate).

| Day | Sessions | Session ## | Active time | Tokens consumed | Cumulative tokens |
|---|---|---|---|---|---|
| 1 | 3 | #1 – #3 | 1h15m | 2h41m (54%) | 2h41m |
| 2 | 3 | #4 – #6 | 1h15m | 2h41m (54%) | 5h22m |
| 3 | 3 | #7 – #9 | 1h15m | 2h41m (54%) | 8h03m |
| 4 | 3 | #10 – #12 | 1h15m | 2h41m (54%) | 10h44m |
| 5 | 3 | #13 – #15 | 1h15m | 2h41m (54%) | 13h25m |
| 6 | 3 | #16 – #18 | 1h15m | 2h41m (54%) | 16h06m |
| 7 | 3 | #19 – #21 | 1h15m | 2h41m (54%) | 18h47m |
| 8 | 3 | #22 – #24 | 1h15m | 2h41m (54%) | 21h28m |
| 9 | 3 | #25 – #27 | 1h15m | 2h41m (54%) | 24h09m |
| 10 | 3 | #28 – #30 | 1h15m | 2h41m (54%) | 26h50m |

**Total:** 30 sessions over ~10 days, ~26h50m token budget consumed (out of 50h available across 10 days).

**Tuning formula:** `delay = T * (1440 / target_active - 1)` where `T` = avg session duration and `target_active` = desired daily active minutes (84 min for 60%).

**Calibration after first sessions:**

```bash
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
durations = [sess['duration_sec']/60 for sess in s['sessions']]
avg = sum(durations) / len(durations)
print(f'Session durations (min): {[round(d,1) for d in durations]}')
print(f'Average: {avg:.0f} min')
# 140 min wall-clock = 100% of 5h budget (burn rate 2.14x)
for pct in [0.5, 0.6, 0.7]:
    target_active = 140 * pct  # wall-clock min to consume pct of budget
    delay = avg * (1440 / target_active - 1)
    sessions_per_day = 1440 / (avg + delay)
    print(f'{pct:.0%} target: delay={delay:.0f} min ({delay/60:.1f}h), ~{sessions_per_day:.1f} sessions/day')
"
```

Adjust `session.delay_minutes` in config.yaml — the runner re-reads it before each session.

### 2.5 Review MISSION_DIRECTIVE.md

The mission directive drives what the system investigates. Before unattended runs, ensure:
- Priority areas are correctly ordered
- Information source URLs are current
- Testing environment names match config.yaml

### 2.6 Ensure QMD Daemon Persistence

QMD must stay running across sessions. Add to `~/.bashrc` if not already there:

```bash
if ! qmd status 2>/dev/null | grep -q "MCP: running"; then
  qmd mcp --http --daemon
fi
```

Or run it in a tmux/screen session:

```bash
tmux new -d -s qmd 'qmd mcp --http'
```

### 2.7 Make the Script Executable

```bash
chmod +x expert-system/scripts/run-sessions.sh
```

---

## 3. Starting the Runner

### 3.1 Dry Run (always do this first)

Preview what would happen without executing any Claude sessions:

```bash
./expert-system/scripts/run-sessions.sh --dry-run
```

This shows:
- Preflight check results
- Config values being used
- The exact prompt that would be sent to each session
- The `claude` command that would be executed

Review the bootstrap prompt (session 1) carefully.

### 3.2 Single Session Test

Run just one session to verify everything works end-to-end:

```bash
./expert-system/scripts/run-sessions.sh --sessions 1
```

After it completes, verify:
- `expert-system/logs/session-001-*.json` exists and contains output
- `expert-system/logs/runner-state.json` shows session_number: 1
- Vault files were created (`_SESSION_BRIEFING.md`, `_INVESTIGATION_AGENDA.md`, etc.)
- SQLite tables were initialized

### 3.3 Full Unattended Run

Run in a terminal multiplexer so it survives SSH disconnects:

```bash
# Option A: tmux
tmux new -s expert
./expert-system/scripts/run-sessions.sh
# Ctrl+B, D to detach — reconnect later with: tmux attach -t expert

# Option B: screen
screen -S expert
./expert-system/scripts/run-sessions.sh
# Ctrl+A, D to detach — reconnect later with: screen -r expert

# Option C: nohup (simplest, no reattach)
nohup ./expert-system/scripts/run-sessions.sh > expert-system/logs/runner.log 2>&1 &
echo $! > expert-system/logs/runner.pid
```

### 3.4 Run a Specific Number of Sessions

```bash
# Run exactly 5 sessions then stop
./expert-system/scripts/run-sessions.sh --sessions 5
```

---

## 4. Monitoring

### 4.1 Live Session Output

Watch the current session's log as it runs:

```bash
# Find the latest log file
ls -t expert-system/logs/session-*.json | head -1

# Tail it
tail -f "$(ls -t expert-system/logs/session-*.json | head -1)"
```

### 4.2 Runner State

Check overall progress:

```bash
cat expert-system/logs/runner-state.json | python3 -m json.tool
```

Shows: current session number, consecutive failures, and per-session history (timestamp, exit code, duration).

Quick summary:

```bash
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
print(f'Sessions completed: {s[\"session_number\"]}')
print(f'Consecutive failures: {s[\"consecutive_failures\"]}')
if s['sessions']:
    last = s['sessions'][-1]
    print(f'Last session: #{last[\"session\"]} at {last[\"timestamp\"]} (exit {last[\"exit_code\"]}, {last[\"duration_sec\"]}s)')
"
```

### 4.3 Knowledge Progress

**Vault briefing** — what the system did and plans to do next:

```bash
# Via Obsidian: open _SESSION_BRIEFING.md
# Via terminal:
cat expert-system/vault/_SESSION_BRIEFING.md
```

**Coverage** — how much of the codebase has been investigated:

```bash
cat expert-system/vault/_KNOWLEDGE_COVERAGE.md
```

**Agenda** — what's planned for upcoming sessions:

```bash
cat expert-system/vault/_INVESTIGATION_AGENDA.md
```

**Vault size** — how many notes have been created:

```bash
find expert-system/vault -name "*.md" | wc -l
find expert-system/vault -name "*.md" -newer expert-system/vault/_SESSION_BRIEFING.md
```

### 4.4 SQLite Metrics

```bash
sqlite3 expert-system/analytics.db "
  SELECT 'Notes analyzed' as metric, count(*) as value FROM analysis_runs
  UNION ALL SELECT 'Modules tracked', count(*) FROM module_health
  UNION ALL SELECT 'Design issues', count(*) FROM design_issues
  UNION ALL SELECT 'External refs', count(*) FROM external_refs
  UNION ALL SELECT 'Exploration findings', count(*) FROM exploration_findings;
"
```

### 4.5 Obsidian Graph View

Open Obsidian with the vault at `expert-system/vault/`. The graph view shows how knowledge nodes are interconnected. A healthy knowledge base shows dense clusters, not isolated nodes.

---

## 5. Controlling the Runner

### 5.1 Graceful Stop

Create the stop file — the runner finishes the current session, then exits:

```bash
touch expert-system/.stop
```

The runner checks for this file before each new session. Remove it to allow future runs:

```bash
rm expert-system/.stop
```

### 5.2 Immediate Stop

Kill the runner process (the current Claude session will also terminate):

```bash
# If using tmux: Ctrl+C in the tmux session
# If using nohup:
kill $(cat expert-system/logs/runner.pid)
```

### 5.3 Pause and Resume

The runner automatically resumes from where it left off — `runner-state.json` tracks the session counter. Just stop the runner (gracefully or immediately) and start it again later:

```bash
# Stop
touch expert-system/.stop
# ... wait for current session to finish ...

# Resume (remove stop file first)
rm expert-system/.stop
./expert-system/scripts/run-sessions.sh
```

### 5.4 Adjust Mid-Run

You can edit `config.yaml` between sessions (the runner re-reads it before each session):

- **Change delay**: edit `session.delay_minutes`
- **Switch to hybrid**: set `autonomy.mode: "hybrid"` — runner will abort at preflight
- **Enable Phase B**: set `phase.current: "generation"` and `phase.generation_allowed: true`
- **Allow mutations**: set `autonomy.allow_api_mutations: true`

You can also edit vault files between sessions:

- **Reprioritize**: edit `_INVESTIGATION_AGENDA.md` to change what gets investigated next
- **Add context**: add notes to the vault — the system discovers them via QMD
- **Redirect**: edit `_SESSION_BRIEFING.md` to leave instructions for the next session

### 5.5 Reset State

To start the session counter from scratch (e.g., after a failed first run):

```bash
rm expert-system/logs/runner-state.json
# Optionally clear old logs:
rm expert-system/logs/session-*.json
```

---

## 6. Stop Conditions

The runner stops automatically when any of these conditions is met:

| Condition | Default | How to change |
|-----------|---------|---------------|
| Stop file exists | `expert-system/.stop` | `touch` / `rm` the file |
| Max sessions reached | 30 | `autonomy.max_sessions` in config.yaml or `--sessions N` flag |
| N consecutive failures | 3 | `autonomy.consecutive_failure_limit` in config.yaml |

Set `max_sessions: 0` for unlimited sessions (will run until another condition triggers).

---

## 7. Safety Model

### What the system CAN do autonomously

- Read and analyze the local code clone
- Read documentation from Confluence, GitLab, Figma, Qase
- Send GET requests to Swagger/API endpoints on testing environments
- Run SELECT queries on the PostgreSQL testing database
- Navigate and screenshot the UI via `playwright-vpn` MCP (the built-in Playwright plugin cannot reach VPN hosts — see `docs/playwright-mcp-fix.md`)
- Create and update vault notes
- Insert and update SQLite records
- Run QMD searches and embeddings

### What the system CANNOT do by default

- **No API mutations** — POST, PUT, PATCH, DELETE are blocked unless `allow_api_mutations: true`
- **No database writes** — only SELECT queries
- **No production access** — testing environments only (enforced by MCP server config)
- **No Phase B auto-start** — must be enabled via `auto_phase_transition: true` or manually

### Permission mode

The runner uses `--permission-mode bypassPermissions`. This is safe because:
- MCP servers enforce access boundaries (read-only DB, testing envs only)
- `allow_api_mutations: false` adds an additional prompt-level gate
- The system operates on a local code clone, not the live repository
- Vault writes are additive (notes), not destructive

If you prefer tighter control, you can switch to hybrid mode (`autonomy.mode: "hybrid"`) which requires human approval at every decision point.

---

## 8. Troubleshooting

### Runner won't start

```
FATAL: autonomy.mode is 'hybrid', expected 'full'
```
Set `autonomy.mode: "full"` in config.yaml.

```
FATAL: python3 pyyaml not installed
```
Run: `pip3 install --break-system-packages pyyaml`

```
FATAL: claude CLI not found
```
Ensure Claude Code is installed and in PATH.

### Sessions failing immediately

Check the latest session log:

```bash
cat "$(ls -t expert-system/logs/session-*.json | head -1)" | python3 -m json.tool
```

Common causes:
- **QMD daemon not running**: `qmd mcp --http --daemon`
- **MCP server crashed**: `claude mcp list` to check, restart as needed

### Consecutive failure limit hit

```bash
# Check what failed
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
for sess in s['sessions'][-5:]:
    print(f'Session {sess[\"session\"]}: exit={sess[\"exit_code\"]} duration={sess[\"duration_sec\"]}s')
"
```

Fix the underlying issue, then either:
- Reset the failure counter by editing `runner-state.json` (set `consecutive_failures: 0`)
- Or delete `runner-state.json` and restart (loses session history)

### No UI exploration happening

Sessions skip Playwright entirely if `playwright-vpn` MCP isn't registered or fails to start:

```bash
# Verify registration
claude mcp get playwright-vpn

# If missing, register it (see docs/playwright-mcp-fix.md):
npm install --prefix .claude/mcp-tools @playwright/mcp
claude mcp add-json playwright-vpn '{
  "command": "/usr/local/bin/node",
  "args": [
    ".claude/mcp-tools/node_modules/@playwright/mcp/cli.js",
    "--browser", "chrome", "--headless", "--no-sandbox",
    "--ignore-https-errors", "--proxy-bypass", "*.noveogroup.com",
    "--viewport-size", "1280x720"
  ],
  "env": { "HTTP_PROXY": "", "HTTPS_PROXY": "", "NO_PROXY": "*.noveogroup.com" }
}' --scope local
```

**Important:** Do NOT use the built-in Playwright plugin (`playwright@claude-plugins-official`) for TTT environments — it inherits `HTTP_PROXY` and gets 502/ERR_CONNECTION_RESET on all VPN hosts.

### Sessions producing no vault updates

- Check that mcp-obsidian is registered: `claude mcp get obsidian`
- Check vault permissions: `ls -la expert-system/vault/`
- Read the session log for errors

---

## 9. Typical Workflow

### Week 1: Bootstrap and Orientation

```bash
# Day 1: Verify setup, dry run, single session test
./expert-system/scripts/run-sessions.sh --dry-run
./expert-system/scripts/run-sessions.sh --sessions 1

# Review results in Obsidian, check SQLite
# Adjust MISSION_DIRECTIVE.md if needed

# Day 1-2: Run 3-5 sessions for orientation
./expert-system/scripts/run-sessions.sh --sessions 5
```

### Week 2-3: Deep Investigation

```bash
# Let it run 15-20 sessions over several days
tmux new -s expert
./expert-system/scripts/run-sessions.sh

# Monitor daily:
cat expert-system/logs/runner-state.json | python3 -m json.tool
cat expert-system/vault/_KNOWLEDGE_COVERAGE.md
```

### Week 3-4: Coverage Review and Phase B

```bash
# Review coverage
cat expert-system/vault/_KNOWLEDGE_COVERAGE.md

# If coverage is sufficient, enable Phase B:
# Edit config.yaml:
#   phase.current: "generation"
#   phase.generation_allowed: true

# Run generation sessions
./expert-system/scripts/run-sessions.sh --sessions 10
```

---

## 10. File Reference

| File | Purpose |
|------|---------|
| `expert-system/config.yaml` | All configuration including autonomy settings |
| `expert-system/scripts/run-sessions.sh` | The runner script |
| `expert-system/logs/runner-state.json` | Session counter, failure tracking |
| `expert-system/logs/session-NNN-*.json` | Per-session Claude output logs |
| `expert-system/.stop` | Touch to gracefully stop the runner |
| `expert-system/vault/_SESSION_BRIEFING.md` | What happened last, what's next |
| `expert-system/vault/_INVESTIGATION_AGENDA.md` | Prioritized investigation items |
| `expert-system/vault/_KNOWLEDGE_COVERAGE.md` | Coverage metrics |
| `CLAUDE+.md` | Implementation prompt (has autonomy-conditional logic) |
