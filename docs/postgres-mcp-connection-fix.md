# Fix: crystaldba/postgres-mcp Connection Failures in Claude Code

## Problem

The `crystaldba/postgres-mcp` MCP server fails to connect to PostgreSQL. In Claude Code, `/mcp` shows the server status as "connecting" then "failed". Restarting sometimes helps, sometimes doesn't.

Tested on: Ubuntu, Cachy OS (Arch). Affects any project using this MCP server.

## Root Causes

There are **three** independent causes that can each prevent connection:

| # | Cause | Symptom |
|---|-------|---------|
| 1 | **Missing `uvx`** — `uv` package manager not installed | `command not found: uvx` |
| 2 | **Cold-start timeout** — `uvx` downloads 64 Python packages on first run, exceeding Claude Code's MCP startup timeout | Server appears to start then times out |
| 3 | **TCP timeout mismatch** — no `libpq` connection params in `DATABASE_URI`, system TCP defaults too short/long | Intermittent connect failures |
| 4 | **Proxy interference** — corporate proxy intercepts TCP to DB host | Connection refused or timeout |

## Fix — Complete Step-by-Step

Apply **all steps in order**. Each step addresses a different root cause.

### Step 1: Install `uv` (provides `uvx`)

Check if `uvx` is available:

```bash
which uvx
```

If not found, install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This installs `uv` and `uvx` to `~/.local/bin/`. Verify:

```bash
~/.local/bin/uvx --version
```

### Step 2: Pre-install `postgres-mcp` as a persistent tool

This eliminates the cold-start download that causes timeout. Without this, `uvx` downloads 64 packages every fresh session.

```bash
~/.local/bin/uv tool install postgres-mcp
```

Expected output: `Installed 64 packages ... Installed 1 executable: postgres-mcp`

### Step 3: Build the DATABASE_URI

Construct the URI from your environment's DB config (found in `e2e/config/ttt/envs/{env}.yml`):

```
postgresql://{dbUsername}:{dbPassword}@{dbHost}:{dbPort}/{initialDatabase}?connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3
```

#### libpq Parameter Reference

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `connect_timeout` | `10` | Wait up to 10s for initial TCP connection |
| `keepalives` | `1` | Enable TCP keepalive probes |
| `keepalives_idle` | `30` | First keepalive probe after 30s idle |
| `keepalives_interval` | `10` | Retry keepalive every 10s if no response |
| `keepalives_count` | `3` | Close connection after 3 unanswered probes |

### Step 4: Update `.claude/.mcp.json` (project-level config)

Use the **full absolute path** to `uvx` — do NOT rely on PATH resolution (Claude Code may not inherit your shell PATH).

Find the full path:

```bash
which uvx   # e.g. /home/youruser/.local/bin/uvx
```

Update the `postgres` entry in `.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "/home/youruser/.local/bin/uvx",
      "args": ["postgres-mcp", "--access-mode=restricted"],
      "env": {
        "DATABASE_URI": "postgresql://user:pass@host:port/dbname?connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3",
        "NO_PROXY": "db-host-or-ip",
        "no_proxy": "db-host-or-ip",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": ""
      }
    }
  }
}
```

Key points:
- **`command`**: full path to `uvx` (e.g., `/home/v/.local/bin/uvx`)
- **`NO_PROXY` / `no_proxy`**: set to the DB host IP to bypass corporate proxy
- **`HTTP_PROXY` / `HTTPS_PROXY`**: set to empty string to prevent proxy interference

### Step 5: Register local-scope config via CLI

Claude Code uses **both** project-level (`.claude/.mcp.json`) and local-scope (`~/.claude.json`) configs. Update both:

```bash
claude mcp remove postgres

claude mcp add-json postgres '{
  "type": "stdio",
  "command": "/home/youruser/.local/bin/uvx",
  "args": ["postgres-mcp", "--access-mode=restricted"],
  "env": {
    "DATABASE_URI": "postgresql://user:pass@host:port/dbname?connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3",
    "NO_PROXY": "db-host-or-ip",
    "no_proxy": "db-host-or-ip",
    "HTTP_PROXY": "",
    "HTTPS_PROXY": ""
  }
}'
```

### Step 6: Verify

Test the connection manually before restarting Claude Code:

```bash
DATABASE_URI="postgresql://user:pass@host:port/dbname?connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3" \
  timeout 30 /home/youruser/.local/bin/uvx postgres-mcp --access-mode=restricted 2>&1
```

Expected output:

```
INFO  Starting PostgreSQL MCP Server in RESTRICTED mode
INFO  Successfully connected to database and initialized connection pool
```

Then restart Claude Code and check `/mcp` — postgres should show as connected.

## Working Example (qa-1 environment)

```json
{
  "postgres": {
    "type": "stdio",
    "command": "/home/v/.local/bin/uvx",
    "args": ["postgres-mcp", "--access-mode=restricted"],
    "env": {
      "DATABASE_URI": "postgresql://ttt:123456@10.0.4.220:5433/ttt?connect_timeout=10&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3",
      "NO_PROXY": "10.0.4.220",
      "no_proxy": "10.0.4.220",
      "HTTP_PROXY": "",
      "HTTPS_PROXY": ""
    }
  }
}
```

## AI Prompt

Use the following prompt to have Claude Code apply this fix automatically on a new machine:

```
Fix my crystaldba/postgres-mcp MCP server connection following docs/fix/postgres-mcp-connection-fix.md.

1. Install uv if missing: curl -LsSf https://astral.sh/uv/install.sh | sh
2. Pre-install postgres-mcp: uv tool install postgres-mcp
3. Get DB credentials from e2e/config/ttt/envs/{env}.yml (env is configured in e2e/config/ttt/ttt.yml)
4. Build DATABASE_URI with libpq params: connect_timeout=10, keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3
5. Update .claude/.mcp.json — use FULL PATH to uvx, add proxy bypass env vars
6. Register local-scope config: claude mcp remove postgres + claude mcp add-json
7. Verify: run uvx postgres-mcp manually and confirm "Successfully connected" output
```

## Troubleshooting

| Issue | Check |
|-------|-------|
| `command not found: uvx` | Step 1 — install uv |
| Timeout on first run | Step 2 — pre-install with `uv tool install postgres-mcp` |
| `connection refused` | Check VPN is active, DB host is reachable: `timeout 5 bash -c 'echo > /dev/tcp/HOST/PORT'` |
| Works manually but fails in Claude Code | Step 4 — use full absolute path to `uvx`, not just `uvx` |
| Intermittent failures | Step 3 — verify libpq params are in the URI query string |
| Proxy-related timeout | Step 4 — add `NO_PROXY`/`no_proxy` with the DB host IP |
