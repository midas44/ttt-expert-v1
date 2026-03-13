# Playwright MCP: Proxy Bypass Fix for VPN Hosts

## Problem

This machine uses `HTTP_PROXY=http://127.0.0.1:2080` for internet access. TTT environments (`*.noveogroup.com`) are behind VPN and must be accessed **directly**, bypassing the proxy.

The **built-in Playwright MCP plugin** (`playwright@claude-plugins-official`) inherits the parent process environment, including `HTTP_PROXY`. It provides no mechanism to override proxy settings or pass browser launch flags. When Chromium tries to reach a VPN host through the proxy:

- `ttt-qa-1.noveogroup.com` → **502 Bad Gateway** (proxy can't reach VPN-only IP)
- `ttt-timemachine.noveogroup.com` → **ERR_CONNECTION_RESET**
- `ttt-stage.noveogroup.com` → **ERR_CONNECTION_RESET**

This makes the built-in plugin unusable for all TTT environments.

### Previous Workaround

Standalone Node.js scripts that `delete process.env.HTTP_PROXY` before launching Chromium (template: `.claude/skills/playwright-browser/scripts/ttt-template.mjs`). This works but loses the interactive snapshot/click/fill MCP tool cycle — each script is fire-and-forget.

## Fix

Register `@playwright/mcp` (the official standalone Playwright MCP server package) as a **regular MCP server** with proxy bypass environment variables and Chromium `--proxy-bypass` flag.

### Installation

```bash
# Install the package locally (avoids npx proxy issues)
npm install --prefix .claude/mcp-tools @playwright/mcp

# Register as local-scope MCP server
claude mcp add-json playwright-vpn '{
  "command": "/usr/local/bin/node",
  "args": [
    ".claude/mcp-tools/node_modules/@playwright/mcp/cli.js",
    "--browser", "chrome",
    "--headless",
    "--no-sandbox",
    "--ignore-https-errors",
    "--proxy-bypass", "*.noveogroup.com",
    "--viewport-size", "1280x720"
  ],
  "env": {
    "HTTP_PROXY": "",
    "HTTPS_PROXY": "",
    "NO_PROXY": "*.noveogroup.com"
  }
}' --scope local
```

### Why It Works

Three layers of proxy bypass:

1. **`HTTP_PROXY=""`** — clears the proxy env var for the Node.js MCP server process, so the Playwright library itself doesn't route through the proxy.
2. **`NO_PROXY=*.noveogroup.com`** — standard env var telling HTTP clients to skip proxy for matching domains.
3. **`--proxy-bypass *.noveogroup.com`** — Chromium-level flag passed to the browser, ensuring the browser engine itself bypasses proxy for VPN hosts.

### Verification

After restarting Claude Code:

```
ToolSearch: select:mcp__playwright-vpn__browser_navigate
→ mcp__playwright-vpn__browser_navigate({ url: "https://ttt-qa-1.noveogroup.com" })
```

Expected: page loads with title "TTT | Noveo".

### Test Results (2026-03-12)

| Env | URL | Built-in Plugin | playwright-vpn |
|-----|-----|----------------|----------------|
| qa-1 | `ttt-qa-1.noveogroup.com` | 502 Bad Gateway | OK |
| timemachine | `ttt-timemachine.noveogroup.com` | ERR_CONNECTION_RESET | OK |
| stage | `ttt-stage.noveogroup.com` | ERR_CONNECTION_RESET | OK |

## Usage

The `playwright-vpn` server exposes the same tools as the built-in plugin, prefixed with `mcp__playwright-vpn__`:

| Tool | Description |
|------|-------------|
| `browser_navigate` | Navigate to a URL |
| `browser_snapshot` | Get accessibility snapshot (preferred for actions) |
| `browser_click` | Click element by ref |
| `browser_fill_form` | Fill form fields |
| `browser_type` | Type text |
| `browser_take_screenshot` | Take screenshot |
| `browser_press_key` | Press keyboard key |
| `browser_hover` | Hover over element |
| `browser_select_option` | Select dropdown option |
| `browser_evaluate` | Run JS on page |
| `browser_wait_for` | Wait for condition |
| `browser_close` | Close page |
| `browser_tabs` | List tabs |
| `browser_console_messages` | Get console output |
| `browser_network_requests` | Get network log |

### When to Use Which

| Approach | Use For |
|----------|---------|
| **`playwright-vpn` MCP** | All TTT environments, interactive exploration, autonomous sessions |
| **Built-in plugin** | Public websites not behind VPN (if needed at all) |
| **Standalone scripts** | Complex multi-page flows, batch screenshots, custom Playwright API usage |

The `playwright-vpn` server is the primary approach for autonomous multi-session execution since it supports the full interactive MCP tool cycle (navigate → snapshot → click → fill → screenshot) without proxy issues.
