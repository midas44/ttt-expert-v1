# Swagger & MCP DNS Fix — /etc/hosts Requirement

> **Purpose:** Documents why all TTT test environment hostnames must be in `/etc/hosts` and how to add them when setting up a new environment.

---

## Problem

Node.js MCP server processes (Swagger, Playwright) fail to resolve VPN hostnames with `getaddrinfo ENOTFOUND`, even when:
- `HTTP_PROXY` and `HTTPS_PROXY` are set to empty strings
- `NO_PROXY=*.noveogroup.com` is configured
- `getent hosts <hostname>` resolves correctly from the shell

The failure is intermittent and affects long-running Node.js processes differently than one-shot commands. `curl` and fresh `node` processes may resolve fine while MCP server processes (which run for the entire Claude Code session) cache a failed DNS lookup from startup.

## Root Cause

VPN DNS resolution is unreliable for long-running Node.js processes. The system `getaddrinfo(3)` call used by Node.js's `uv_getaddrinfo` behaves differently from `getent hosts` (which uses NSS directly). When the VPN DNS resolver is slow or flaky at process startup, the failure gets cached and persists for the lifetime of the process.

## Solution

Add all TTT environment hostnames to `/etc/hosts`. This makes DNS resolution instant and reliable for all tools (Node.js, curl, Python, etc.) regardless of VPN DNS state.

### Current entries required

```
10.0.4.220 ttt-qa-1.noveogroup.com
10.0.6.53  ttt-timemachine.noveogroup.com
10.0.4.241 ttt-stage.noveogroup.com
```

### How to add

```bash
echo '10.0.4.220 ttt-qa-1.noveogroup.com
10.0.6.53  ttt-timemachine.noveogroup.com
10.0.4.241 ttt-stage.noveogroup.com' | sudo tee -a /etc/hosts
```

### Verify

```bash
grep noveogroup /etc/hosts
node -e "const dns = require('dns'); dns.lookup('ttt-timemachine.noveogroup.com', (e,a) => console.log(e ? e.code : a))"
```

---

## Adding a New Test Environment (HUMAN STEP REQUIRED)

When a new TTT test environment is added to `expert-system/config.yaml` and `config/ttt/envs/<name>.yml`:

1. **Find the IP** — check the `dbHost` field in `config/ttt/envs/<name>.yml`
2. **Add to /etc/hosts** — requires `sudo`:

   ```bash
   echo '<IP> ttt-<name>.noveogroup.com' | sudo tee -a /etc/hosts
   ```

3. **Verify** — `getent hosts ttt-<name>.noveogroup.com` and Node.js lookup both return the IP
4. **Register MCP servers** — run Swagger/Postgres sync scripts, restart Claude Code

**This step cannot be automated by the AI** because `sudo` requires an interactive terminal with a password. The AI will detect the missing `/etc/hosts` entry (Swagger calls fail with `ENOTFOUND`) and instruct the human to add it.

---

## Affected MCP Types

| MCP Type | Resolves hostname via | Affected by VPN DNS flakiness |
|----------|----------------------|-------------------------------|
| **Swagger** (21 servers) | Node.js `getaddrinfo` at API call time | Yes — fails with `ENOTFOUND` |
| **Playwright-VPN** | Chromium's DNS resolver | Yes — but less frequent |
| **PostgreSQL** (3 servers) | Uses IP addresses directly from env config | No — bypasses DNS entirely |

PostgreSQL servers connect by IP (from `config/ttt/envs/<name>.yml` → `dbHost`), so they don't need `/etc/hosts` entries. Swagger and Playwright use hostnames and are affected.

---

## Verification Matrix

After setup, all combinations should work:

| MCP | qa-1 | timemachine | stage |
|-----|------|-------------|-------|
| Swagger | `mcp__swagger-qa1-ttt-api__get-project-types-using-get` | `mcp__swagger-tm-ttt-api__get-project-types-using-get` | `mcp__swagger-stage-ttt-api__get-project-types-using-get` |
| Postgres | `mcp__postgres-qa1__list_schemas` | `mcp__postgres-tm__list_schemas` | `mcp__postgres-stage__list_schemas` |
| Playwright | Navigate to `https://ttt-qa-1.noveogroup.com/report` | Navigate to `https://ttt-timemachine.noveogroup.com/report` | Navigate to `https://ttt-stage.noveogroup.com/report` |
