# Fix: Swagger MCP Server Connection Failures in Claude Code

## Problem

Swagger MCP servers (powered by `@ivotoby/openapi-mcp-server`) fail to connect on Claude Code startup. In `/mcp` they show as "failed" or "connecting". Affects any of the 21 swagger servers across qa-1, timemachine, and stage environments.

## Root Causes

There are **four** independent causes:

| # | Cause | Symptom |
|---|-------|---------|
| 1 | **Missing local-scope registration** — server only in `.claude/.mcp.json`, not registered via `claude mcp add-json` | Server silently ignored on startup |
| 2 | **Bare `npx` command** — Claude Code may not resolve shell PATH on startup | `command not found: npx` or timeout |
| 3 | **Cold-start + intermittent 502** — the swagger spec endpoint returns 502 transiently; MCP server fetches the spec on startup and exits immediately on failure | Startup fails, manual retry sometimes works |
| 4 | **Flaky DNS resolution** — `curl` inside the wrapper script intermittently fails to resolve VPN hostnames (e.g. `ttt-stage.noveogroup.com`) even though `getent hosts` returns the correct IP. This is distinct from proxy issues — the hostname simply fails to resolve via curl's internal resolver. | `Could not resolve host` error, HTTP 000 in <5ms |

### Cause 3 in detail

The MCP config sets `HTTP_PROXY=""` to bypass the corporate proxy for VPN-accessible hosts (`*.noveogroup.com`). But `npx -y @ivotoby/openapi-mcp-server` needs the proxy to reach npmjs.org to verify/download the package. With proxy disabled, `npx` can't resolve the package.

### Cause 4 in detail

The system has `HTTP_PROXY=http://127.0.0.1:2080` configured. VPN hosts resolve to internal IPs (10.x.x.x) via the VPN DNS. However, `curl` occasionally uses a different DNS code path that resolves to the public IP or fails entirely, even when:
- `/etc/hosts` has the correct mapping
- `getent hosts` returns the correct IP
- Environment proxy vars are unset

The fix is to pre-resolve the hostname via `getent hosts` and pass `--resolve host:port:ip` to curl, bypassing its internal resolver entirely. Additionally, `--noproxy '*'` (wildcard) is more reliable than `--noproxy "${NO_PROXY}"` with specific patterns.

## Current Architecture

### 21 Swagger MCP Servers

Naming convention: `swagger-{env}-{service}-{group}` where:
- **env**: `qa1`, `tm` (timemachine), `stage`
- **service**: `ttt`, `vacation`, `calendar`, `email`
- **group**: `api`, `test`, `default`

Each server uses the same wrapper script but with different env vars (`OPENAPI_SPEC_PATH`, `API_BASE_URL`, `API_HEADERS`, `SERVER_NAME`).

### File Inventory

| File | Purpose |
|------|---------|
| `.claude/mcp-tools/start-swagger-mcp.sh` | Wrapper script (DNS resolve + retry + cache + launch) |
| `.claude/mcp-tools/node_modules/` | Pre-installed `@ivotoby/openapi-mcp-server` |
| `.claude/mcp-tools/cache/swagger-spec-{SERVER_NAME}.json` | Per-server cached swagger spec (auto-refreshed) |
| `.claude/.mcp.json` | Project-scope MCP config (21 swagger + 3 postgres + gitlab + confluence + figma) |
| `~/.claude.json` (projects section) | Local-scope MCP config (registered via `claude mcp add-json`) |

## Fix — Complete Step-by-Step

### Step 1: Pre-install the package locally

Install `@ivotoby/openapi-mcp-server` into a local `node_modules` so `npx` is no longer needed:

```bash
mkdir -p /home/v/Dev/ttt-expert-v1/.claude/mcp-tools
npm install --prefix /home/v/Dev/ttt-expert-v1/.claude/mcp-tools @ivotoby/openapi-mcp-server
```

This creates the binary at:
```
.claude/mcp-tools/node_modules/@ivotoby/openapi-mcp-server/bin/mcp-server.js
```

### Step 2: Create wrapper script with DNS resolve + retry + cache

The wrapper script lives at `.claude/mcp-tools/start-swagger-mcp.sh`. Key features:

1. **DNS resolution** via `getent hosts` — reads `/etc/hosts` and system DNS reliably
2. **`--resolve` flag** — pins curl to the resolved IP, bypassing curl's flaky DNS
3. **`--noproxy '*'`** — wildcard proxy bypass (more reliable than host-specific patterns)
4. **Per-server cache** — each server gets its own cache file named `swagger-spec-{SERVER_NAME}.json`
5. **Retry on cold start** — up to 5 attempts × 3s delay when no cache exists
6. **Non-blocking refresh** — one quick attempt when cache exists; uses stale cache on failure

Current wrapper script:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
CACHE_FILE="$CACHE_DIR/swagger-spec-${SERVER_NAME:-default}.json"
SPEC_URL="${OPENAPI_SPEC_PATH:-}"
MAX_RETRIES=5
RETRY_DELAY=3

mkdir -p "$CACHE_DIR"

resolve_host() {
    # Extract hostname from URL, resolve via getent (reads /etc/hosts + DNS)
    local url="$1"
    local host port
    host=$(echo "$url" | sed -n 's|^https\?://\([^/:]*\).*|\1|p')
    [[ "$url" == https://* ]] && port=443 || port=80
    local ip
    ip=$(getent hosts "$host" 2>/dev/null | awk '{print $1; exit}')
    if [[ -n "$ip" && "$ip" != "$host" ]]; then
        echo "--resolve ${host}:${port}:${ip}"
    fi
}

fetch_spec() {
    local url="$1"
    local out="$2"
    local resolve_arg
    resolve_arg=$(resolve_host "$url")
    # shellcheck disable=SC2086
    curl --noproxy '*' \
         -sf --max-time 15 \
         $resolve_arg \
         -o "$out" \
         "$url" 2>/dev/null
}

validate_json() {
    python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$1" 2>/dev/null
}

try_fetch_and_cache() {
    local temp="$CACHE_DIR/.swagger-spec-temp.json"
    if fetch_spec "$SPEC_URL" "$temp" && validate_json "$temp"; then
        mv "$temp" "$CACHE_FILE"
        return 0
    fi
    rm -f "$temp"
    return 1
}

if [[ -n "$SPEC_URL" && "$SPEC_URL" == http* ]]; then
    if [[ -f "$CACHE_FILE" ]]; then
        try_fetch_and_cache || true
    else
        for i in $(seq 1 "$MAX_RETRIES"); do
            try_fetch_and_cache && break
            [[ $i -lt $MAX_RETRIES ]] && sleep "$RETRY_DELAY"
        done
    fi
fi

if [[ -f "$CACHE_FILE" ]]; then
    export OPENAPI_SPEC_PATH="$CACHE_FILE"
fi

exec /usr/local/bin/node "$SCRIPT_DIR/node_modules/@ivotoby/openapi-mcp-server/bin/mcp-server.js"
```

Make executable:

```bash
chmod +x /home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh
```

### Step 3: Configure MCP servers in `.claude/.mcp.json`

Each swagger server entry looks like:

```json
{
  "swagger-{env}-{service}-{group}": {
    "type": "stdio",
    "command": "/usr/bin/bash",
    "args": ["/home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh"],
    "env": {
      "OPENAPI_SPEC_PATH": "https://ttt-{env-full}.noveogroup.com/api/{service}/v2/api-docs?group={group}",
      "API_BASE_URL": "https://ttt-{env-full}.noveogroup.com/api/{service}",
      "API_HEADERS": "API_SECRET_TOKEN:{api-key}",
      "SERVER_NAME": "swagger-{env}-{service}-{group}",
      "NO_PROXY": "*.noveogroup.com",
      "no_proxy": "*.noveogroup.com",
      "HTTP_PROXY": "",
      "HTTPS_PROXY": ""
    }
  }
}
```

Key points:
- **`command`**: full path `/usr/bin/bash` (not bare `bash`)
- **`args`**: full path to wrapper script
- **`SERVER_NAME`**: must match the JSON key — used for per-server cache file naming
- **`OPENAPI_SPEC_PATH`**: the remote URL — the wrapper overrides it with the cached file on startup

### Step 4: Register all servers in local scope

All 21 servers must be registered via `claude mcp add-json` for reliable loading:

```bash
# Programmatic registration of all swagger servers from .mcp.json
node -e "
const { execSync } = require('child_process');
const mcp = require('./.claude/.mcp.json');
const servers = Object.entries(mcp.mcpServers).filter(([k]) => k.startsWith('swagger-'));
for (const [name, config] of servers) {
  execSync('claude mcp add-json ' + name + ' ' + JSON.stringify(JSON.stringify(config)) + ' -s local', { stdio: 'inherit' });
}
console.log('Registered', servers.length, 'swagger servers');
"
```

### Step 5: Seed caches (first time or after failures)

The wrapper auto-caches on first startup, but if an environment is unreachable, you may need to seed manually:

```bash
# Seed a specific cache with pinned DNS resolution
env -u HTTP_PROXY -u HTTPS_PROXY curl -sk \
  --resolve "ttt-stage.noveogroup.com:443:10.0.4.241" \
  -o .claude/mcp-tools/cache/swagger-spec-swagger-stage-ttt-api.json \
  "https://ttt-stage.noveogroup.com/api/ttt/v2/api-docs?group=api"
```

### Step 6: Verify

```bash
# Check all caches exist (should be 21 files)
ls -1 .claude/mcp-tools/cache/swagger-spec-swagger-*.json | wc -l

# Validate a specific cache
python3 -c "import json; d=json.load(open('.claude/mcp-tools/cache/swagger-spec-swagger-stage-ttt-api.json')); print(f'Swagger {d[\"swagger\"]}, {len(d[\"paths\"])} paths')"
```

Then restart Claude Code and check `/mcp` — all swagger servers should show as connected.

## How the cache works

```
Startup with cache (typical, <1s):
  1. resolve_host() → getent hosts → get IP for hostname
  2. Try refresh from remote URL with --resolve host:port:ip (one attempt, non-blocking)
  3. On success → update cache; on failure → keep existing cache
  4. Set OPENAPI_SPEC_PATH to local cache file
  5. Start MCP server → instant, reads local JSON file

Startup without cache (first time only, up to ~18s):
  1. resolve_host() → getent hosts → get IP for hostname
  2. Retry remote URL up to 5 times × 3s delay, each with --resolve
  3. On success → create cache → start server with local file
  4. On failure → start server with remote URL (likely fails too)
```

## Comparison with postgres-mcp fix

Both fixes follow the same pattern:

| Aspect | postgres-mcp | swagger servers |
|--------|-------------|-----------------|
| Pre-install | `uv tool install postgres-mcp` | `npm install --prefix .claude/mcp-tools` |
| Full path | `/home/v/.local/bin/uvx` | `/usr/bin/bash` → wrapper script |
| Proxy bypass | `NO_PROXY` + empty `HTTP_PROXY` | Same + wrapper uses `--noproxy '*'` + `--resolve` |
| DNS fix | Direct IP in DATABASE_URI | `getent hosts` → `--resolve host:port:ip` |
| Extra | libpq timeout params in URI | Spec caching with retry logic |
| Local-scope | `claude mcp add-json` | Same (21 servers) |
| Auto-config | `node .claude/scripts/sync-postgres-mcp.js --apply` | Manual (21 servers registered programmatically) |

## DNS Issues — /etc/hosts

Some VPN hostnames don't resolve correctly via the system DNS. Known entries needed in `/etc/hosts`:

```
10.0.4.220 ttt-qa-1.noveogroup.com
```

Check if other hosts resolve to internal IPs:

```bash
getent hosts ttt-timemachine.noveogroup.com  # should be 10.0.6.53
getent hosts ttt-stage.noveogroup.com        # should be 10.0.4.241
getent hosts ttt-qa-1.noveogroup.com         # should be 10.0.4.220
```

If any resolve to a public IP (80.x.x.x), add a `/etc/hosts` entry.

## Troubleshooting

| Issue | Check |
|-------|-------|
| Server fails on startup, no cache | Seed cache manually (Step 5) with `--resolve` |
| Cache is stale / API changed | Delete specific cache file and restart |
| `Could not resolve host` | Add `/etc/hosts` entry or check VPN connection |
| `node: command not found` | Verify `/usr/local/bin/node` exists; update path in wrapper script |
| Works manually but fails in Claude Code | Verify both `.claude/.mcp.json` and `claude mcp add-json` registration match |
| New endpoints missing | Cache auto-refreshes on each startup when the remote is available |
| Specific env servers fail, others work | Check DNS: `getent hosts ttt-{env}.noveogroup.com` — must be internal IP |
| HTTP 502 on qa-1 only | Check `/etc/hosts` — qa-1 may resolve to public IP without it |
