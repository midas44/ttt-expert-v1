---
name: mcp-setup
description: >
  Install, configure, and troubleshoot MCP (Model Context Protocol) servers in Claude Code
  at the project level. Use this skill when the user asks to add a new MCP server, connect
  Claude Code to a Swagger/OpenAPI API, configure an MCP integration, fix broken MCP servers,
  or troubleshoot MCP servers not appearing in /mcp. Also use when the user mentions
  "mcp add", "mcp server", "swagger mcp", "openapi mcp", or wants to connect Claude Code
  to an external API, database, or tool via MCP. Covers scopes (local, project, user),
  proxy/VPN issues, authentication headers, and the critical distinction between project-scope
  (.mcp.json) and local-scope (~/.claude.json) server registration.
---

# MCP Server Setup & Troubleshooting

## Key Concepts

### MCP Scopes

Claude Code supports three MCP server scopes:

| Scope | Storage Location | Shared? | Needs Approval? |
|-------|-----------------|---------|-----------------|
| **Local** (default) | `~/.claude.json` under project path | No | No |
| **Project** | `.mcp.json` at project root | Yes (git) | Yes |
| **User** | `~/.claude.json` global | No | No |

**Critical:** Project-scoped servers (`.mcp.json`) require per-server approval stored in `~/.claude.json` under `projects[path].enabledMcpjsonServers`. If this array is empty, NO project servers load — even if `enableAllProjectMcpServers: true` is set in `settings.local.json`.

### Reliable Registration Method

Always use `claude mcp add` or `claude mcp add-json` CLI commands. These register servers as **local-scoped** in `~/.claude.json`, which requires no approval and loads reliably.

Do NOT rely solely on `.claude/.mcp.json` or `.claude/settings.local.json` — the approval mechanism can silently prevent servers from loading.

## Adding an MCP Server

### Step 1: Identify the server type

- **npm package** (stdio): `npx -y <package-name>`
- **Python package** (stdio): `uvx <package-name>`
- **Remote HTTP**: Direct URL
- **Remote SSE**: Direct URL (deprecated, prefer HTTP)

### Step 2: Register via CLI

Use `claude mcp add-json` for full control over config:

```bash
claude mcp add-json <server-name> '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "<package-name>"],
  "env": {
    "KEY": "value"
  }
}'
```

Or use `claude mcp add` for simpler cases:

```bash
# HTTP remote server
claude mcp add --transport http <name> <url>

# stdio with env vars
claude mcp add --transport stdio --env API_KEY=xxx <name> -- npx -y <package>

# With auth header (HTTP)
claude mcp add --transport http <name> <url> --header "Authorization: Bearer token"
```

### Step 3: Verify

```bash
claude mcp list
claude mcp get <server-name>
```

Then restart Claude Code and check with `/mcp`.

## Adding a Swagger/OpenAPI MCP Server

Use `@ivotoby/openapi-mcp-server` — it reads Swagger/OpenAPI specs and exposes every endpoint as a callable MCP tool.

### Find the spec URL

For Spring Boot apps, check the swagger-resources endpoint:

```bash
curl -s <base-url>/swagger-resources
```

Common spec URL patterns:
- Swagger 2.0: `/v2/api-docs` or `/v2/api-docs?group=<name>`
- OpenAPI 3.0: `/v3/api-docs` or `/v3/api-docs/<name>`

### Register the server

```bash
claude mcp add-json <name> '{
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@ivotoby/openapi-mcp-server"],
  "env": {
    "OPENAPI_SPEC_PATH": "<spec-json-url>",
    "API_BASE_URL": "<api-base-url>",
    "API_HEADERS": "<header-name>:<header-value>",
    "SERVER_NAME": "<name>"
  }
}'
```

### Verify spec is reachable

Before registering, test that the spec endpoint returns valid JSON:

```bash
curl -s -w "\n%{http_code}" -H "<AuthHeader>: <token>" "<spec-url>" | tail -1
```

Expected: `200` with JSON response containing `"swagger":"2.0"` or `"openapi":"3.0..."`.

## Proxy / VPN Configuration

When Claude Code runs behind a proxy (`HTTP_PROXY`/`HTTPS_PROXY`) but the MCP target is on a VPN (no proxy needed), add proxy-bypass env vars to the server config:

```json
{
  "env": {
    "NO_PROXY": "*.internal.company.com,host1.company.com",
    "no_proxy": "*.internal.company.com,host1.company.com",
    "HTTP_PROXY": "",
    "HTTPS_PROXY": ""
  }
}
```

Setting `HTTP_PROXY` and `HTTPS_PROXY` to empty strings in the server env overrides the inherited proxy for that specific MCP server process.

**Test connectivity** before registering:

```bash
# With proxy bypass
curl -s --noproxy "target-host.com" -o /dev/null -w "%{http_code}" "https://target-host.com/endpoint"
```

## Troubleshooting

### Servers not appearing in `/mcp`

1. **Check `~/.claude.json`** — look at `projects[path].mcpServers` and `projects[path].enabledMcpjsonServers`:

```bash
cat ~/.claude.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
p = d.get('projects', {}).get('$(pwd)', {})
print('mcpServers:', list(p.get('mcpServers', {}).keys()))
print('enabledMcpjsonServers:', p.get('enabledMcpjsonServers', []))
"
```

2. **If `enabledMcpjsonServers` is empty** — project-scoped servers from `.mcp.json` won't load. Fix: re-register servers with `claude mcp add-json` (local scope).

3. **If `mcpServers` is empty** — no local-scoped servers registered. Fix: use `claude mcp add-json`.

4. **Reset project approval state** if needed:

```bash
claude mcp reset-project-choices
```

### Server fails to start

Test the server manually with the same env vars:

```bash
OPENAPI_SPEC_PATH="..." API_BASE_URL="..." \
  timeout 15 npx -y @ivotoby/openapi-mcp-server 2>&1 | head -30
```

Look for:
- `error: missing required argument` — wrong package or missing config
- Connection errors — proxy/VPN/auth issues
- `Registered tool:` lines — success

### `/plugin` vs `/mcp`

- `/plugin` — shows marketplace plugins (curated extensions), NOT raw MCP servers
- `/mcp` — shows all MCP servers (local, project, user, cloud-synced)

Always use `/mcp` to check MCP server status.

## Managing Servers

```bash
# List all servers
claude mcp list

# Get details
claude mcp get <name>

# Remove a server
claude mcp remove <name>

# Reset project .mcp.json approval choices
claude mcp reset-project-choices
```

## Reference: MCP Config Locations

| File | Purpose |
|------|---------|
| `~/.claude.json` → `projects[path].mcpServers` | Local-scoped servers (per-project, private) |
| `~/.claude.json` → `projects[path].enabledMcpjsonServers` | Approval list for project-scoped servers |
| `<project>/.mcp.json` | Project-scoped servers (shared via git, needs approval) |
| `~/.claude/settings.json` | Global user settings (NOT for MCP servers) |
| `<project>/.claude/settings.local.json` | Project-local settings overrides |
| `/etc/claude-code/managed-mcp.json` | Managed/organizational MCP config (admin-deployed) |
