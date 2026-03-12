---
name: swagger-api
description: >
  Call TTT (Time Tracking Tool) REST API endpoints on testing environments via Swagger MCP tools
  or curl. Use this skill when the user asks to call a TTT API endpoint, test an API, use
  Swagger, interact with the TTT backend, manipulate the test clock, sync employees/projects,
  trigger notifications, or execute any endpoint from the TTT Swagger spec. Also use when
  the user mentions "call endpoint", "test API", "swagger", "clock", "sync employees",
  "sync projects", "send notifications", "reset clock", "patch clock", or references
  ttt-qa-1/ttt-qa-2/ttt-timemachine/ttt-stage environments. This skill covers all services
  and Swagger groups across all environments.
---

# TTT Swagger API

## MCP Server Naming Convention

All Swagger MCP servers follow the pattern: `swagger-{env}-{service}-{group}`

| Segment | Values |
|---------|--------|
| **env** | `qa1`, `tm` (timemachine), `stage` |
| **service** | `ttt`, `vacation`, `calendar`, `email` |
| **group** | `api`, `test` (test-api), `default` |

**Examples:** `swagger-qa1-ttt-test`, `swagger-tm-vacation-default`, `swagger-stage-email-api`

MCP tool prefix: `mcp__swagger-{env}-{service}-{group}__`

## Environments & API Keys

API keys are passed via the `API_SECRET_TOKEN` header. Keys are stored in `config/ttt/envs/<name>.yml`.

| Env | URL pattern | API Key |
|-----|-------------|---------|
| qa-1 | `https://ttt-qa-1.noveogroup.com/api/{service}` | `76c45e8c-457a-4a8f-817f-4160d0cc2eaf` |
| timemachine | `https://ttt-timemachine.noveogroup.com/api/{service}` | `c603661a-9057-42b9-b216-88e95784b9a0` |
| stage | `https://ttt-stage.noveogroup.com/api/{service}` | `aec4212b-f480-4491-9f71-a38db8619e3a` |

## Available Swagger Groups (per env)

| Service | Group | MCP suffix | Description |
|---------|-------|------------|-------------|
| ttt | api | `-ttt-api` | Main production API endpoints |
| ttt | test-api | `-ttt-test` | Test/dev endpoints (clock, sync, notifications) |
| vacation | default | `-vacation-default` | Vacation service endpoints |
| vacation | test-api | `-vacation-test` | Vacation test endpoints |
| calendar | default | `-calendar-default` | Calendar service endpoints |
| email | api | `-email-api` | Email service endpoints |
| email | test-api | `-email-test` | Email test endpoints |

## Calling Endpoints

### Method 1: MCP Tools (preferred for GET and no-body POST)

MCP tools are available with prefix `mcp__swagger-{env}-{service}-{group}__`. Example for qa-1 ttt test-api:

```
mcp__swagger-qa1-ttt-test__get-using-get-5              → GET /v1/test/clock
mcp__swagger-qa1-ttt-test__reset-using-pst              → POST /v1/test/clock/reset
mcp__swagger-qa1-ttt-test__get-current-roles-using-get   → GET /v1/test/employees/current/roles
```

Works reliably for:
- All `GET` endpoints
- `POST` endpoints without request bodies

### Method 2: curl (required for PATCH/POST with request bodies)

The MCP server has a known issue serializing JSON request bodies (the `request` parameter schema defaults to string due to circular `$ref` in the Swagger spec). Use curl as fallback:

```bash
curl -s --noproxy "*.noveogroup.com" \
  -X <METHOD> \
  -H "Content-Type: application/json" \
  -H "API_SECRET_TOKEN: <api-key-from-env-config>" \
  -d '<json-body>' \
  "https://ttt-<env>.noveogroup.com/api/<service><path>"
```

**Important:** Always use `--noproxy "*.noveogroup.com"` because the machine has a proxy configured but the servers are on VPN (no proxy needed).

## Endpoint Reference: ttt test-api

### Clock

| MCP Tool | Method | Path | Body | Description |
|----------|--------|------|------|-------------|
| `get-using-get-5` | GET | `/v1/test/clock` | — | Get current server clock |
| `ptch-using-ptch-11` | PATCH | `/v1/test/clock` | `{"time":"<ISO>"}` | Set clock to specific time (**use curl**) |
| `reset-using-pst` | POST | `/v1/test/clock/reset` | — | Reset clock to real time |

**Clock PATCH example (curl, qa-1):**

```bash
curl -s --noproxy "*.noveogroup.com" -X PATCH \
  -H "Content-Type: application/json" \
  -H "API_SECRET_TOKEN: 76c45e8c-457a-4a8f-817f-4160d0cc2eaf" \
  -d '{"time":"2026-02-28T12:00:00"}' \
  "https://ttt-qa-1.noveogroup.com/api/ttt/v1/test/clock"
```

The `time` field uses ISO 8601 format without timezone: `YYYY-MM-DDTHH:mm:ss`.

### Employees

| MCP Tool | Method | Path | Body | Description |
|----------|--------|------|------|-------------|
| `get-current-roles-using-get` | GET | `/v1/test/employees/current/roles` | — | Get current user's roles |
| `find-roles-by-login-using-get` | GET | `/v1/test/employees/{login}/roles` | — | Get roles by login |
| `sync-using-pst-1` | POST | `/v1/test/employees/sync` | query: `fullSync=true/false` | Sync employees with CS |

### Projects

| MCP Tool | Method | Path | Body | Description |
|----------|--------|------|------|-------------|
| `sync-using-pst-2` | POST | `/v1/test/project/sync` | — | Sync projects with PM |

### Notifications

| MCP Tool | Method | Path | Description |
|----------|--------|------|-------------|
| `send-notifications-using-pst` | POST | `/v1/test/budgets/notify` | Over-budget notifications |
| `send-reports-changed-notifications-using-pst` | POST | `/v1/test/reports/notify-changed` | Changed report notification |
| `send-reports-forgotten-notifications-using-pst` | POST | `/v1/test/reports/notify-forgotten` | Forgotten reports notification |
| `send-reports-forgotten-delayed-notifications-using-pst` | POST | `/v1/test/reports/notify-forgotten-delayed` | Delayed forgotten notification |
| `send-reject-notifications-using-pst` | POST | `/v1/test/reports/notify-rejected` | Rejected report notification |

### Other

| MCP Tool | Method | Path | Description |
|----------|--------|------|-------------|
| `trigger-pre-release-test-using-get` | GET | `/v1/test/pre-release` | Pre-release test message |
| `clean-up-using-pst` | POST | `/v1/test/reports/cleanup-extended` | Clean up extended report time |
| `trigger-optimized-statistic-report-sync-using-pst` | POST | `/v1/test/statistic-reports` | Sync statistic report cache |

## Connection Architecture

All 21 Swagger MCP servers use a shared wrapper script at `.claude/mcp-tools/start-swagger-mcp.sh`. The wrapper handles three problems that cause raw `@ivotoby/openapi-mcp-server` to fail:

1. **Spec caching** — fetches the swagger JSON spec once and caches it locally per server. Subsequent startups use the cache (instant) and attempt a non-blocking refresh.
2. **DNS resolution** — uses `getent hosts` to pre-resolve VPN hostnames, then passes `--resolve host:port:ip` to curl. This bypasses intermittent DNS failures where curl's own resolver fails to resolve VPN hosts.
3. **Retry logic** — retries up to 5 times on first-time cache build (when the spec endpoint returns 502 transiently).

### Cache Files

Cache directory: `.claude/mcp-tools/cache/`

Each server gets its own file: `swagger-spec-{SERVER_NAME}.json`

Example: `swagger-spec-swagger-stage-ttt-api.json`

### Troubleshooting Connection Failures

| Symptom | Fix |
|---------|-----|
| Server shows "failed" in `/mcp` | Check cache exists: `ls .claude/mcp-tools/cache/swagger-spec-swagger-{env}-{service}-{group}.json` |
| No cache file for a server | Seed manually: `curl -sk --resolve "host:443:ip" -o cache/swagger-spec-{name}.json "spec-url"` |
| All servers for one env fail | Check DNS: `getent hosts ttt-{env}.noveogroup.com` — must resolve to internal IP |
| qa-1 servers fail with 502 | Verify `/etc/hosts` has `10.0.4.220 ttt-qa-1.noveogroup.com` |
| MCP tool returns stale data | Delete the cache file and restart Claude Code |

For full details see `docs/swagger-mcp-connection-fix.md`.

## Discovering New Endpoints

```bash
# List available API groups for a service on an env
curl -s --noproxy "*.noveogroup.com" \
  "https://ttt-qa-1.noveogroup.com/api/ttt/swagger-resources"

# Fetch full spec for a group
curl -s --noproxy "*.noveogroup.com" \
  -H "API_SECRET_TOKEN: 76c45e8c-457a-4a8f-817f-4160d0cc2eaf" \
  "https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=api" | python3 -m json.tool
```

## Common Patterns

### Shift clock forward by N days (qa-1)

1. Get current time: call `mcp__swagger-qa1-ttt-test__get-using-get-5`
2. Calculate new time: add N days to the returned timestamp
3. Patch clock via curl with the new timestamp
4. Verify: call `mcp__swagger-qa1-ttt-test__get-using-get-5` again

### Reset after testing

Always reset the clock after time-dependent tests:

```
call mcp__swagger-qa1-ttt-test__reset-using-pst
```

### Check authentication

If endpoints return 401/403, verify the API key is correct by calling a simple GET:

```
call mcp__swagger-qa1-ttt-test__get-using-get-5
```

If this works, auth is fine — the issue is likely with how the request body is sent.

### Switching environments

To use a different environment, change the env prefix in the MCP tool name:
- qa-1: `mcp__swagger-qa1-ttt-test__...`
- timemachine: `mcp__swagger-tm-ttt-test__...`
- stage: `mcp__swagger-stage-ttt-test__...`
