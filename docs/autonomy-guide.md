# Autonomy Mode Guide — Running the Expert System Unattended

> **Purpose:** Step-by-step guide for preparing, launching, monitoring, and managing the expert system in fully autonomous mode — where sessions run unattended via a shell loop.
>
> **Prerequisite:** The base expert system must already be set up per `docs/human-guide.md`. This guide covers only the autonomy-specific additions.
>
> **Billing:** This system is designed for the Claude MAX plan subscription. The MAX plan has a 5h token budget per usage window (~4.8 windows/day). The inter-session delay is tuned to consume ~64% of each window's budget, leaving headroom for interactive use.

---

## 1. How It Works

In autonomous mode, a shell script (`expert-system/scripts/run-sessions.sh`) launches sequential `claude -p` sessions. Each session:

1. Reads `CLAUDE.md` + `config.yaml` (autonomy.mode = "full")
2. Reads vault state (`_SESSION_BRIEFING.md`, `_INVESTIGATION_AGENDA.md`, etc.)
3. Picks top investigation items, executes them without waiting for human approval
4. Updates vault notes, SQLite, and coverage tracking
5. Exits

The master prompt lives in `CLAUDE+.md`. Claude Code only reads `CLAUDE.md` at session start, so the runner creates a `CLAUDE.md -> CLAUDE+.md` symlink before sessions begin and removes it on exit. This keeps the master prompt active during autonomous runs without polluting interactive sessions.

The script captures exit codes, enforces stop conditions via timeout, and maintains a state file (`runner-state.json`) across sessions. Each session's stdout (JSON) and stderr (diagnostics) are written to separate files. After each session, vault changes are auto-committed to a local git repo for per-session history. Cross-session memory lives entirely in the vault and SQLite — each `claude -p` invocation is stateless.

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

# Verify /etc/hosts has all TTT environments (critical for Swagger MCPs)
grep noveogroup /etc/hosts
# Must show entries for ALL environments in config.yaml:
#   10.0.4.220 ttt-qa-1.noveogroup.com
#   10.0.6.53  ttt-timemachine.noveogroup.com
#   10.0.4.241 ttt-stage.noveogroup.com
# If missing, add them — see docs/swagger-api-connection-fix.md
```

> **Adding a new environment?** After adding it to `config.yaml` and `config/ttt/envs/<name>.yml`, you **must manually** add its `/etc/hosts` entry (`sudo` required — the AI cannot do this). Without it, all Swagger and Playwright MCP calls to that environment will fail with `ENOTFOUND`. See `docs/swagger-api-connection-fix.md`.

### 2.2 Review config.yaml

The `autonomy` section in `expert-system/config.yaml`:

```yaml
autonomy:
  mode: "full"                       # "hybrid" or "full"
  max_sessions: 30                   # Stop after N sessions (0 = unlimited)
  consecutive_failure_limit: 3       # Abort after N consecutive failures
  auto_phase_transition: false       # Auto-switch to Phase B when coverage target met
  log_dir: "expert-system/logs"      # Session log directory
  stop: false                        # Set to true to gracefully stop after current session
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
| `session.delay_minutes` | 70 | See §2.3 for tuning guidance |
| `session.delay_minutes_offhours` | 45 | Off-hours delay; see §2.3 |
| `session.offhours_utc` | 15:00-03:00 | UTC range for off-hours delay |

### 2.3 Session Delay and Token Budget

#### Understanding the budget model

The MAX plan has a **5h token budget per usage window** (not per day). There are approximately **4.8 usage windows per day** (24h / 5h). Each window's budget resets independently.

Empirically, **uninterrupted Claude Code work burns through the 5h token budget in ~2h20m of wall-clock time** (burn rate ~2.14x). This means each 30-min expert session consumes approximately 64 min of the 5h (300 min) token budget.

#### Sessions per usage window

| Sessions/window | Token consumption | % of 5h budget | Headroom for interactive use |
|---|---|---|---|
| 2 | 128 min | 43% | 172 min (57%) |
| **3** | **193 min** | **64%** | **107 min (36%)** |
| 4 | 257 min | 86% | 43 min (14%) |
| 5 | 321 min | **exceeds budget** | — |

**Recommended: 3 sessions per window** — uses ~64% of budget, leaves headroom for interactive use.

#### Delay calculation

To fit N sessions evenly within a 5h (300 min) window:

```
cycle = 300 / N                    # minutes between session starts
delay = cycle - avg_session_time   # gap between sessions
```

| Target sessions/window | Cycle time | Delay (T=30min) | Sessions/day | Days for 100 sessions |
|---|---|---|---|---|
| 2 | 150 min | **120 min** | ~9.6 | ~10.4 |
| **3** | **100 min** | **70 min** | **~14.4** | **~6.9** |
| 4 | 75 min | 45 min | ~19.2 | ~5.2 |

The default `delay_minutes: 70` targets 3 sessions per usage window (~14 sessions/day, ~64% budget consumption).

#### Impact of session duration (delay = 70 min)

| Avg session | Sessions/window | Token consumption/window | Sessions/day | Days for 100 |
|---|---|---|---|---|
| 15 min | 3.5 | 96 min (32%) | ~17 | ~5.9 |
| 20 min | 3.3 | 129 min (43%) | ~16 | ~6.3 |
| **30 min** | **3.0** | **193 min (64%)** | **~14** | **~7.1** |
| 45 min | 2.6 | 241 min (80%) | ~12.5 | ~8.0 |
| 60 min | 2.3 | 308 min (**over!**) | ~11 | ~9.1 |

> **Warning:** If sessions average >50 min, the 70 min delay may exceed the window budget. Increase the delay or reduce session duration via `max_duration_minutes`.

#### Calibration after first sessions

```bash
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
durations = [sess['duration_sec']/60 for sess in s['sessions']]
avg = sum(durations) / len(durations)
print(f'Session durations (min): {[round(d,1) for d in durations]}')
print(f'Average: {avg:.0f} min')
print()
# Budget model: 5h (300 min) token window, burn rate 2.14x
for n in [2, 3, 4]:
    cycle = 300 / n
    delay = cycle - avg
    token_per_window = n * avg * 2.14
    pct = token_per_window / 300
    sessions_per_day = 1440 / (avg + max(delay, 0))
    status = 'OK' if pct < 0.9 else 'OVER BUDGET'
    print(f'{n} sessions/window: delay={delay:.0f} min, {pct:.0%} budget, ~{sessions_per_day:.0f}/day [{status}]')
"
```

Adjust `session.delay_minutes` in config.yaml — the runner re-reads it before each session.

#### Off-hours optimization

During non-working hours (default: 15:00–03:00 UTC), there's no need for interactive headroom. The runner automatically uses `delay_minutes_offhours` (45 min) instead of `delay_minutes` (70 min), fitting 4 sessions per window instead of 3.

| Period | Hours (UTC) | Delay | Sessions/window | Budget usage | Sessions in period |
|---|---|---|---|---|---|
| Working | 03:00–15:00 | 70 min | 3 | 64% | ~7.2 |
| Off-hours | 15:00–03:00 | 45 min | 4 | 86% | ~9.6 |
| **Daily total** | — | — | — | — | **~16.8** |

The `offhours_utc` range in config.yaml uses `HH:MM-HH:MM` format (UTC). Overnight ranges (start > end) are handled correctly — e.g., `15:00-03:00` means hour >= 15 OR hour < 3.

### 2.5 Review MISSION_DIRECTIVE.md

The mission directive drives what the system investigates. Before unattended runs, ensure:
- Priority areas are correctly ordered
- Information source URLs are current
- Testing environment names match config.yaml

### 2.6 QMD Daemon

The runner's preflight check now auto-detects whether the QMD MCP daemon is running (via `pgrep -f "qmd.*mcp"`). If it's not running, the runner starts it automatically with `qmd mcp --http --daemon`. If auto-start fails, the runner continues with a warning — semantic search will be unavailable but sessions will still work.

For extra reliability, you can also keep QMD running persistently:

```bash
# Option A: tmux
tmux new -d -s qmd 'qmd mcp --http'

# Option B: ~/.bashrc auto-start
if ! pgrep -f "qmd.*mcp" >/dev/null 2>&1; then
  qmd mcp --http --daemon
fi
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
- CLAUDE.md symlink creation (and removal on exit via trap)
- Preflight check results (including QMD daemon auto-start)
- Config values being used, including session timeout
- The exact prompt that would be sent to each session
- The `claude` command with timeout that would be executed

Review the bootstrap prompt (session 1) carefully. After the dry run exits, verify `CLAUDE.md` was cleaned up: `ls -la CLAUDE.md` should show "No such file".

### 3.2 Single Session Test

Run just one session to verify everything works end-to-end:

```bash
./expert-system/scripts/run-sessions.sh --sessions 1
```

After it completes, verify:

```bash
# Session JSON output is valid
python3 -m json.tool "$(ls -t expert-system/logs/session-*.json | head -1)" > /dev/null

# Stderr log exists (may be empty if no warnings)
ls -la "$(ls -t expert-system/logs/session-*.stderr | head -1)"

# Runner log captured all output
cat expert-system/logs/runner.log

# State file updated
python3 -m json.tool expert-system/logs/runner-state.json

# CLAUDE.md symlink cleaned up
ls -la CLAUDE.md  # should be gone

# Vault files were created
ls expert-system/vault/_SESSION_BRIEFING.md

# SQLite tables initialized
sqlite3 expert-system/analytics.db ".tables"

# Vault git commit recorded
git -C expert-system/vault log --oneline -1
```

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
# Runner log is auto-persisted to expert-system/logs/runner.log
nohup ./expert-system/scripts/run-sessions.sh > /dev/null 2>&1 &
echo $! > expert-system/logs/runner.pid
```

### 3.4 Run a Specific Number of Sessions

```bash
# Run exactly 5 sessions then stop
./expert-system/scripts/run-sessions.sh --sessions 5
```

---

## 4. Monitoring

### 4.1 Live Output

**Runner log** — the runner's own timestamped messages (persisted automatically):

```bash
tail -f expert-system/logs/runner.log
```

**Current session stdout** (JSON output from Claude):

```bash
tail -f "$(ls -t expert-system/logs/session-*.json | head -1)"
```

**Current session stderr** (MCP warnings, Node.js errors, diagnostics):

```bash
tail -f "$(ls -t expert-system/logs/session-*.stderr | head -1)"
```

Session output is split into paired files: `session-001-*.json` (clean JSON) + `session-001-*.stderr` (diagnostics). This prevents MCP warnings from corrupting the JSON output.

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

**Vault history** — what each session contributed (via per-session git commits):

```bash
git -C expert-system/vault log --oneline --stat
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

### 4.5 Coverage Report

Run the coverage estimation script for a comprehensive Phase A dashboard:

```bash
./expert-system/scripts/coverage-report.sh
```

This queries SQLite + counts vault notes to produce:
- Module health completeness (rows with key fields filled)
- External refs by source type (Confluence, GitLab, Figma, Qase)
- Exploration findings by method (UI, API, DB)
- Vault note count by directory
- Wikilink density (average `[[...]]` links per note)
- Weighted composite score (target: >=80% for Phase A completion)

### 4.6 Obsidian Graph View

Open Obsidian with the vault at `expert-system/vault/`. The graph view shows how knowledge nodes are interconnected. A healthy knowledge base shows dense clusters, not isolated nodes.

---

## 5. Controlling the Runner

### 5.1 Graceful Stop

Set `autonomy.stop: true` in `config.yaml` — the runner finishes the current session, then exits:

```yaml
# expert-system/config.yaml
autonomy:
  stop: true   # was false
```

The runner re-reads config before each new session. Set it back to `false` to allow future runs.

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
# Stop: set autonomy.stop: true in config.yaml
# ... wait for current session to finish ...

# Resume: set autonomy.stop: false in config.yaml
./expert-system/scripts/run-sessions.sh
```

### 5.4 Adjust Mid-Run

You can edit `config.yaml` between sessions (the runner re-reads it before each session):

- **Change delay**: edit `session.delay_minutes` and/or `session.delay_minutes_offhours`
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
rm expert-system/logs/session-*.json expert-system/logs/session-*.stderr
rm expert-system/logs/runner.log
```

---

## 6. Stop Conditions

The runner stops automatically when any of these conditions is met:

| Condition | Default | How to change |
|-----------|---------|---------------|
| `autonomy.stop` is true | `false` | Set to `true` in config.yaml |
| Max sessions reached | 30 | `autonomy.max_sessions` in config.yaml or `--sessions N` flag |
| N consecutive failures | 3 | `autonomy.consecutive_failure_limit` in config.yaml |
| Session timeout | max_duration + 30 min | `session.max_duration_minutes` in config.yaml |

Set `max_sessions: 0` for unlimited sessions (will run until another condition triggers).

**Session timeout:** Each `claude -p` call is wrapped with `timeout`. If a session exceeds `max_duration_minutes + 30` minutes (grace period for cleanup), it's terminated with SIGTERM (then SIGKILL after 60s). Timed-out sessions count as failures (exit code 124) and increment the consecutive failure counter. The default `max_duration_minutes: 240` gives a hard timeout of 270 minutes.

**Completion notification:** When the runner finishes (for any reason), it logs the stop reason and sends a desktop notification via `notify-send` (non-fatal if unavailable). Useful when running in tmux for extended periods.

---

## 7. Safety Model

### What the system CAN do autonomously

- Read and analyze the local code clone
- Read documentation from Confluence, Figma, Qase (via MCP), and GitLab (via curl REST API with PAT — the GitLab MCP server exposes no tools on this CE 16.11 instance)
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

### CLAUDE.md conflict

```
FATAL: CLAUDE.md exists and is not a symlink — refusing to overwrite
```
A real `CLAUDE.md` file exists at the project root. The runner won't overwrite it. Either rename/delete the file, or if you created it intentionally, convert it to a symlink: `ln -sf "CLAUDE+.md" CLAUDE.md`.

### Sessions failing immediately

Check the session log and stderr:

```bash
# JSON output (may be truncated if claude crashed)
python3 -m json.tool "$(ls -t expert-system/logs/session-*.json | head -1)"

# Stderr (MCP errors, Node.js crashes, etc.)
cat "$(ls -t expert-system/logs/session-*.stderr | head -1)"
```

Common causes:
- **QMD daemon not running**: runner auto-starts it, but check `pgrep -f "qmd.*mcp"`
- **MCP server crashed**: `claude mcp list` to check, restart as needed

### Proxy / VPN drops causing timeouts

Claude Code requires `HTTP_PROXY=http://127.0.0.1:2080` (AdGuard VPN in SOCKS mode). If the VPN drops mid-session, the `claude -p` process hangs on API calls until the 270-min timeout kills it.

**Prevention:** A cron-based watchdog checks the proxy every 3 minutes and restarts the VPN if it's down:

```bash
# Add to crontab (crontab -e):
*/3 * * * * /home/v/Dev/ttt-expert-v1/expert-system/scripts/proxy-watchdog.sh >> /home/v/Dev/ttt-expert-v1/expert-system/logs/proxy-watchdog.log 2>&1
```

The watchdog script (`expert-system/scripts/proxy-watchdog.sh`) tests connectivity through the proxy and runs `adguardvpn-cli disconnect && adguardvpn-cli connect -l FI` on failure. Logs only appear when a restart was needed.

**Diagnosis:** If you see a session timeout in `runner-state.json`, check if the proxy was down at that time:

```bash
# Timed-out sessions
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
for sess in s['sessions']:
    if sess['exit_code'] == 124:
        print(f'Session {sess[\"session\"]}: TIMED OUT at {sess[\"timestamp\"]}')
"

# Proxy restart events around that time
grep "Proxy" expert-system/logs/proxy-watchdog.log
```

### Sessions timing out

If sessions consistently hit the timeout (exit code 124), check:
- `max_duration_minutes` in config.yaml — increase if sessions legitimately need more time
- The stderr file for hung MCP calls or infinite loops
- Whether an MCP server is unresponsive (e.g., VPN disconnected)
- Whether the proxy was down (see "Proxy / VPN drops" above)

```bash
# Find timed-out sessions
python3 -c "
import json
with open('expert-system/logs/runner-state.json') as f:
    s = json.load(f)
for sess in s['sessions']:
    if sess['exit_code'] == 124:
        print(f'Session {sess[\"session\"]}: TIMED OUT at {sess[\"timestamp\"]} ({sess[\"duration_sec\"]}s)')
"
```

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

### Day 1: Bootstrap and Orientation

```bash
# Verify setup, dry run, single session test
./expert-system/scripts/run-sessions.sh --dry-run
./expert-system/scripts/run-sessions.sh --sessions 1

# Review results in Obsidian, check SQLite
# Adjust MISSION_DIRECTIVE.md if needed
# Check actual session duration, adjust delay_minutes if needed

# Run 3-5 more sessions for orientation
./expert-system/scripts/run-sessions.sh --sessions 5
```

### Days 2-5: Deep Investigation

```bash
# At ~14 sessions/day, 100 sessions take ~7 days
tmux new -s expert
./expert-system/scripts/run-sessions.sh

# Monitor daily:
cat expert-system/logs/runner-state.json | python3 -m json.tool
cat expert-system/vault/_KNOWLEDGE_COVERAGE.md
./expert-system/scripts/coverage-report.sh
```

### Days 5-7+: Coverage Review and Phase B

Run the coverage report to assess Phase A readiness:

```bash
./expert-system/scripts/coverage-report.sh
```

**Phase A is complete when:**
- Composite score >= 80%
- Note growth rate has plateaued (<2 new notes/session for 3+ consecutive sessions)
- All priority modules (absences, reports, accounting, administration) have entries
- All 4 source types represented in external_refs (Confluence, GitLab, Figma, Qase)
- All 3 exploration methods used (UI, API, DB)

You can also track per-session contributions via vault git history:

```bash
git -C expert-system/vault log --oneline --stat
```

```bash
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
| `expert-system/scripts/coverage-report.sh` | Phase A coverage estimation dashboard |
| `expert-system/scripts/proxy-watchdog.sh` | Cron watchdog — restarts VPN proxy if down |
| `expert-system/logs/proxy-watchdog.log` | Proxy restart events (cron output) |
| `expert-system/logs/runner-state.json` | Session counter, failure tracking |
| `expert-system/logs/runner.log` | Runner's own timestamped log (auto-persisted) |
| `expert-system/logs/session-NNN-*.json` | Per-session Claude stdout (clean JSON) |
| `expert-system/logs/session-NNN-*.stderr` | Per-session stderr (MCP warnings, diagnostics) |
| `expert-system/vault/_SESSION_BRIEFING.md` | What happened last, what's next |
| `expert-system/vault/_INVESTIGATION_AGENDA.md` | Prioritized investigation items |
| `expert-system/vault/_KNOWLEDGE_COVERAGE.md` | Coverage metrics |
| `expert-system/vault/.git` | Vault inner git repo (auto-managed, per-session commits) |
| `artefacts/` | UI screenshots and other exploration artefacts (gitignored) |
| `CLAUDE+.md` | Master prompt (symlinked as `CLAUDE.md` during runner sessions) |
