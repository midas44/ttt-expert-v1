#!/usr/bin/env bash
# Wrapper for @ivotoby/openapi-mcp-server that retries spec fetch
# and falls back to a cached spec file on failure.
#
# Solves: MCP server dies on startup when the swagger endpoint
# returns 502 (slow backend / transient failure).
#
# Behavior:
# - If cache exists: try to refresh once (non-blocking), use cache on failure
# - If no cache: retry up to MAX_RETRIES times to build initial cache
# - Always point MCP server at local file (instant startup)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
CACHE_FILE="$CACHE_DIR/swagger-spec-${SERVER_NAME:-default}.json"
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
