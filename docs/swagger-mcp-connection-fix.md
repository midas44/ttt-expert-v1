# Fix: @ivotoby/openapi-mcp-server (ttt-swagger-test) Connection Failures in Claude Code

## Problem

The `ttt-swagger-test` MCP server fails to connect on Claude Code startup. In `/mcp` it shows as "failed" or "connecting". Manual reconnect (via Claude Code MCP UI) sometimes works.

## Root Causes

There are **three** independent causes, all contributing:

| # | Cause | Symptom |
|---|-------|---------|
| 1 | **Missing local-scope registration** — server only in `.claude/.mcp.json`, not registered via `claude mcp add-json` | Server silently ignored on startup |
| 2 | **Bare `npx` command** — Claude Code may not resolve shell PATH on startup | `command not found: npx` or timeout |
| 3 | **Cold-start + intermittent 502** — `npx -y` downloads the package (needs proxy), but proxy is disabled for VPN hosts; swagger endpoint returns 502 intermittently | Startup fails, manual retry sometimes works |

### Cause 3 in detail

The MCP config sets `HTTP_PROXY=""` to bypass the corporate proxy for VPN-accessible hosts (`*.noveogroup.com`). But `npx -y @ivotoby/openapi-mcp-server` needs the proxy to reach npmjs.org to verify/download the package. With proxy disabled, `npx` can't resolve the package.

Additionally, the swagger spec endpoint (`/api/ttt/v2/api-docs?group=test-api`) intermittently returns HTTP 502 Bad Gateway. The MCP server fetches the spec on startup and exits immediately on failure — no retry logic.

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

### Step 2: Create wrapper script with retry + cache

Create `.claude/mcp-tools/start-swagger-mcp.sh`:

```bash
#!/usr/bin/env bash
# Wrapper for @ivotoby/openapi-mcp-server that retries spec fetch
# and falls back to a cached spec file on failure.
#
# Behavior:
# - If cache exists: try to refresh once (non-blocking), use cache on failure
# - If no cache: retry up to MAX_RETRIES times to build initial cache
# - Always point MCP server at local file (instant startup)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
CACHE_FILE="$CACHE_DIR/swagger-spec-test-api.json"
SPEC_URL="${OPENAPI_SPEC_PATH:-}"
MAX_RETRIES=5
RETRY_DELAY=3

mkdir -p "$CACHE_DIR"

fetch_spec() {
    local url="$1"
    local out="$2"
    curl --noproxy "${NO_PROXY:-}" \
         -sf --max-time 10 \
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
        # Cache exists — try one quick refresh, don't block on failure
        try_fetch_and_cache || true
    else
        # No cache — retry to build initial cache
        for i in $(seq 1 "$MAX_RETRIES"); do
            try_fetch_and_cache && break
            [[ $i -lt $MAX_RETRIES ]] && sleep "$RETRY_DELAY"
        done
    fi
fi

# Use cached spec if available, otherwise let the server try the URL directly
if [[ -f "$CACHE_FILE" ]]; then
    export OPENAPI_SPEC_PATH="$CACHE_FILE"
fi

exec /usr/local/bin/node "$SCRIPT_DIR/node_modules/@ivotoby/openapi-mcp-server/bin/mcp-server.js"
```

Make it executable:

```bash
chmod +x /home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh
```

### Step 3: Seed the cache

Manually fetch the spec once (retry if 502):

```bash
curl --noproxy "ttt-qa-1.noveogroup.com" -sf --max-time 10 \
  -o /home/v/Dev/ttt-expert-v1/.claude/mcp-tools/cache/swagger-spec-test-api.json \
  "https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=test-api"
```

Validate:

```bash
python3 -c "import json; d=json.load(open('.claude/mcp-tools/cache/swagger-spec-test-api.json')); print(f'Swagger {d[\"swagger\"]}, {len(d[\"paths\"])} paths')"
# Expected: Swagger 2.0, 14 paths
```

### Step 4: Update `.claude/.mcp.json`

Replace the `ttt-swagger-test` entry — use full path to bash, point to wrapper script:

```json
{
  "ttt-swagger-test": {
    "type": "stdio",
    "command": "/usr/bin/bash",
    "args": [
      "/home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh"
    ],
    "env": {
      "OPENAPI_SPEC_PATH": "https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=test-api",
      "API_BASE_URL": "https://ttt-qa-1.noveogroup.com/api/ttt",
      "API_HEADERS": "API_SECRET_TOKEN:af38fc55-97a4-4ea3-86c7-c5c80686f6be",
      "SERVER_NAME": "ttt-swagger-test",
      "NO_PROXY": "ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com",
      "no_proxy": "ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com",
      "HTTP_PROXY": "",
      "HTTPS_PROXY": ""
    }
  }
}
```

Key points:
- **`command`**: full path `/usr/bin/bash` (not bare `bash`)
- **`args`**: full path to wrapper script
- **`OPENAPI_SPEC_PATH`**: still the remote URL — the wrapper overrides it with the cached file

### Step 5: Register local-scope config via CLI

```bash
claude mcp remove ttt-swagger-test
claude mcp add-json ttt-swagger-test '{
  "type": "stdio",
  "command": "/usr/bin/bash",
  "args": ["/home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh"],
  "env": {
    "OPENAPI_SPEC_PATH": "https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=test-api",
    "API_BASE_URL": "https://ttt-qa-1.noveogroup.com/api/ttt",
    "API_HEADERS": "API_SECRET_TOKEN:af38fc55-97a4-4ea3-86c7-c5c80686f6be",
    "SERVER_NAME": "ttt-swagger-test",
    "NO_PROXY": "ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com",
    "no_proxy": "ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com",
    "HTTP_PROXY": "",
    "HTTPS_PROXY": ""
  }
}'
```

### Step 6: Verify

Test the wrapper manually:

```bash
OPENAPI_SPEC_PATH="https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=test-api" \
API_BASE_URL="https://ttt-qa-1.noveogroup.com/api/ttt" \
API_HEADERS="API_SECRET_TOKEN:af38fc55-97a4-4ea3-86c7-c5c80686f6be" \
SERVER_NAME="ttt-swagger-test" \
NO_PROXY="ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com" \
no_proxy="ttt-qa-1.noveogroup.com,ttt-qa-2.noveogroup.com,*.noveogroup.com" \
HTTP_PROXY="" HTTPS_PROXY="" \
timeout 10 /usr/bin/bash /home/v/Dev/ttt-expert-v1/.claude/mcp-tools/start-swagger-mcp.sh
```

Expected: no output, exit code 143 (killed by timeout — server was running). If it fails, you'll see an error message before the timeout.

Then restart Claude Code and check `/mcp` — `ttt-swagger-test` should show as connected.

## How the cache works

```
Startup with cache (typical, <1s):
  1. Try refresh from remote URL (one attempt, non-blocking)
  2. On success → update cache; on failure → keep existing cache
  3. Set OPENAPI_SPEC_PATH to local cache file
  4. Start MCP server → instant, reads local JSON file

Startup without cache (first time only, up to ~15s):
  1. Retry remote URL up to 5 times × 3s delay
  2. On success → create cache → start server with local file
  3. On failure → start server with remote URL (likely fails too)
```

## File inventory

| File | Purpose |
|------|---------|
| `.claude/mcp-tools/start-swagger-mcp.sh` | Wrapper script (retry + cache + launch) |
| `.claude/mcp-tools/node_modules/` | Pre-installed `@ivotoby/openapi-mcp-server` |
| `.claude/mcp-tools/cache/swagger-spec-test-api.json` | Cached swagger spec (auto-refreshed) |
| `.claude/.mcp.json` | Project-scope MCP config |
| `~/.claude.json` (projects section) | Local-scope MCP config (registered via `claude mcp add-json`) |

## Comparison with postgres-mcp fix

Both fixes follow the same pattern:

| Aspect | postgres-mcp | ttt-swagger-test |
|--------|-------------|-----------------|
| Pre-install | `uv tool install postgres-mcp` | `npm install --prefix .claude/mcp-tools` |
| Full path | `/home/v/.local/bin/uvx` | `/usr/bin/bash` → wrapper script |
| Proxy bypass | `NO_PROXY` + empty `HTTP_PROXY` | Same + wrapper handles proxy conflict |
| Extra | libpq timeout params in URI | Spec caching with retry logic |
| Local-scope | `claude mcp add-json` | Same |

## Troubleshooting

| Issue | Check |
|-------|-------|
| Server fails on startup, no cache | Run Step 3 manually to seed the cache |
| Cache is stale / API changed | Delete `.claude/mcp-tools/cache/swagger-spec-test-api.json` and restart |
| `node: command not found` | Verify `/usr/local/bin/node` exists; update path in wrapper script |
| Works manually but fails in Claude Code | Verify both `.claude/.mcp.json` and `claude mcp add-json` registration match |
| New endpoints missing | The cache auto-refreshes on each startup when the remote is available |
