---
name: swagger-api
description: >
  Call TTT (Time Tracking Tool) REST API endpoints on the QA environment via Swagger MCP tools
  or curl. Use this skill when the user asks to call a TTT API endpoint, test an API, use
  Swagger, interact with the TTT backend, manipulate the test clock, sync employees/projects,
  trigger notifications, or execute any endpoint from the TTT Swagger spec. Also use when
  the user mentions "call endpoint", "test API", "swagger", "clock", "sync employees",
  "sync projects", "send notifications", "reset clock", "patch clock", or references
  ttt-qa-1/ttt-qa-2 environments. This skill covers both the test-api and api Swagger groups.
---

# TTT Swagger API

## Environments

| Env | Base URL | API Key |
|-----|----------|---------|
| QA-1 | `https://ttt-qa-1.noveogroup.com/api/ttt` | `af38fc55-97a4-4ea3-86c7-c5c80686f6be` |

API keys are passed via the `API_SECRET_TOKEN` header.

## Swagger Spec URLs

Two API groups are available:

| Group | Spec URL | Description |
|-------|----------|-------------|
| **test-api** | `/v2/api-docs?group=test-api` | Test/dev endpoints (clock, sync, notifications) |
| **api** | `/v2/api-docs?group=api` | Main production API endpoints |

The `test-api` group is connected via MCP server `ttt-swagger-test`.

## Calling Endpoints

### Method 1: MCP Tools (preferred for GET and no-body POST)

MCP tools are available with prefix `mcp__ttt-swagger-test__`. Use them directly:

```
mcp__ttt-swagger-test__get-using-get-5          → GET /v1/test/clock
mcp__ttt-swagger-test__reset-using-pst          → POST /v1/test/clock/reset
mcp__ttt-swagger-test__get-current-roles-using-get → GET /v1/test/employees/current/roles
```

Works reliably for:
- All `GET` endpoints
- `POST` endpoints without request bodies

### Method 2: curl (required for PATCH/POST with request bodies)

The MCP server has a known issue serializing JSON request bodies (the `request` parameter schema defaults to string due to circular `$ref` in the Swagger spec). Use curl as fallback:

```bash
curl -s --noproxy "ttt-qa-1.noveogroup.com" \
  -X <METHOD> \
  -H "Content-Type: application/json" \
  -H "API_SECRET_TOKEN: af38fc55-97a4-4ea3-86c7-c5c80686f6be" \
  -d '<json-body>' \
  "https://ttt-qa-1.noveogroup.com/api/ttt<path>"
```

**Important:** Always use `--noproxy "ttt-qa-1.noveogroup.com"` because the machine has a proxy configured but the QA server is on VPN (no proxy needed).

## Endpoint Reference: test-api

### Clock

| MCP Tool | Method | Path | Body | Description |
|----------|--------|------|------|-------------|
| `get-using-get-5` | GET | `/v1/test/clock` | — | Get current server clock |
| `ptch-using-ptch-11` | PATCH | `/v1/test/clock` | `{"time":"<ISO>"}` | Set clock to specific time (**use curl**) |
| `reset-using-pst` | POST | `/v1/test/clock/reset` | — | Reset clock to real time |

**Clock PATCH example (curl):**

```bash
curl -s --noproxy "ttt-qa-1.noveogroup.com" -X PATCH \
  -H "Content-Type: application/json" \
  -H "API_SECRET_TOKEN: af38fc55-97a4-4ea3-86c7-c5c80686f6be" \
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

## Discovering New Endpoints

To check if the Swagger spec has changed or to explore the `api` group:

```bash
# List available API groups
curl -s --noproxy "ttt-qa-1.noveogroup.com" \
  "https://ttt-qa-1.noveogroup.com/api/ttt/swagger-resources"

# Fetch full spec for a group
curl -s --noproxy "ttt-qa-1.noveogroup.com" \
  -H "API_SECRET_TOKEN: af38fc55-97a4-4ea3-86c7-c5c80686f6be" \
  "https://ttt-qa-1.noveogroup.com/api/ttt/v2/api-docs?group=api" | python3 -m json.tool
```

## Common Patterns

### Shift clock forward by N days

1. Get current time: call `get-using-get-5`
2. Calculate new time: add N days to the returned timestamp
3. Patch clock via curl with the new timestamp
4. Verify: call `get-using-get-5` again

### Reset after testing

Always reset the clock after time-dependent tests:

```
call mcp__ttt-swagger-test__reset-using-pst
```

### Check authentication

If endpoints return 401/403, verify the API key is correct by calling a simple GET:

```
call mcp__ttt-swagger-test__get-using-get-5
```

If this works, auth is fine — the issue is likely with how the request body is sent.
