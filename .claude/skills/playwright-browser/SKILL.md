---
name: playwright-browser
description: >
  Automate browser interactions on the TTT QA environment (and other web apps) using
  Playwright — navigate pages, log in, click elements, fill forms, switch language,
  take screenshots, and more. Use this skill when the user asks to "open a page",
  "take a screenshot", "log in as user X", "test in the browser", "navigate to",
  "check the UI", "use Playwright", "browser test", "screenshot a page", or any task
  that requires controlling a real browser. Also use when the user mentions "playwright",
  "headless browser", "browser automation", "open TTT", "login to TTT", "screenshot",
  or asks to visually verify a page. Covers both the Playwright MCP plugin (for simple
  public-site interactions) and standalone Node.js scripts (for VPN/proxy-restricted sites).
---

# Playwright Browser Automation

This skill provides instructions for automating browser interactions using Playwright,
with special handling for the TTT QA environment behind VPN.

## Two Approaches

There are two ways to use Playwright in this project:

| Approach | When to Use | Proxy/VPN Support |
|---|---|---|
| **Playwright MCP plugin** | Simple tasks on public sites (no VPN) | No — inherits `HTTP_PROXY`, cannot bypass |
| **Standalone Node.js script** | VPN sites (`*.noveogroup.com`), complex flows, screenshots to disk | Yes — unsets proxy env vars before launch |

**Important:** The Playwright MCP plugin (`playwright@claude-plugins-official`) inherits
the system `HTTP_PROXY=http://127.0.0.1:2080` at browser launch. VPN-only hosts like
`ttt-qa-1.noveogroup.com` return **502 Bad Gateway** through this proxy. There is no way
to configure proxy bypass in the MCP plugin. **Always use standalone scripts for VPN hosts.**

---

## 1. Standalone Script (Recommended for TTT)

### Prerequisites

Playwright must be installed as a local npm package:

```bash
npm list playwright 2>/dev/null || npm install --no-save playwright
```

The system Chrome (`google-chrome`) is used as the browser via `channel: 'chrome'`.

### Script Template

Use or adapt the bundled template at `scripts/ttt-template.mjs`:

```bash
node <skill-path>/scripts/ttt-template.mjs
```

### Key Patterns

#### Proxy Bypass (CRITICAL for VPN hosts)

Always unset proxy env vars at the top of the script, **before** any Playwright imports
are used to launch browsers:

```js
delete process.env.HTTP_PROXY;
delete process.env.HTTPS_PROXY;
delete process.env.http_proxy;
delete process.env.https_proxy;
```

#### Browser Launch

```js
const browser = await chromium.launch({
  headless: true,
  channel: 'chrome'   // uses system google-chrome
});

const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  ignoreHTTPSErrors: true
});

const page = await context.newPage();
```

#### TTT Login (Login-Only Auth, No Password)

The TTT QA login page has a single `Login` field and a `LOGIN` button — no password.

```js
await page.goto('https://ttt-qa-1.noveogroup.com', { waitUntil: 'networkidle', timeout: 30000 });
await page.fill('#username', '<login>');
await Promise.all([
  page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
  page.click('button[type="submit"]')
]);
// After login, URL should be /report (dashboard)
```

#### Switch Language (RU -> EN)

The nav bar shows "RU" as a dropdown. Click it, then click "EN":

```js
await page.locator('text=RU').first().click();
await page.waitForTimeout(500);
const enOption = page.locator('text=EN').first();
if (await enOption.isVisible({ timeout: 3000 }).catch(() => false)) {
  await enOption.click();
  await page.waitForLoadState('networkidle', { timeout: 15000 });
}
```

If already in English, the nav shows "EN" — skip this step or check first:

```js
const langText = await page.locator('.nav >> text=/^(RU|EN)$/').first().textContent();
if (langText === 'RU') { /* switch */ }
```

#### Navigate to Common Pages

| Page | URL Path | Notes |
|---|---|---|
| Dashboard (My tasks) | `/report` | Default after login |
| My Vacations | `/vacation/my` | Redirects to `/vacation/my/my-vacation/OPENED` |
| Vacation Requests | `/vacation/request` | Shows pending vacation requests |
| Absence Calendar | via nav menu "Calendar of absences" dropdown | |
| Planner | `/planner` | |
| Confirmation | `/confirmation` | |

#### Take Screenshots

```js
await page.screenshot({
  path: 'artifacts/playwright/screenshot-name.png',
  fullPage: true
});
```

Always save to `artifacts/playwright/`. Create the directory first if needed.

#### Logout

```js
await page.goto('https://cas-demo.noveogroup.com/logout', {
  waitUntil: 'networkidle', timeout: 30000
});
```

The page should contain "Logout successful".

#### Error Handling

Always wrap in try/catch and take an error screenshot on failure:

```js
try {
  // ... steps ...
} catch (error) {
  console.error(`Error: ${error.message}`);
  await page.screenshot({ path: 'artifacts/playwright/error-screenshot.png', fullPage: true });
} finally {
  await browser.close();
}
```

---

## 2. Playwright MCP Plugin (Public Sites Only)

The MCP plugin is useful for quick interactions with public websites that don't require
VPN access.

### Available MCP Tools

| Tool | Description |
|---|---|
| `browser_navigate` | Navigate to a URL |
| `browser_click` | Click an element by ref |
| `browser_fill_form` | Fill form fields |
| `browser_type` | Type text into focused element |
| `browser_press_key` | Press keyboard key |
| `browser_hover` | Hover over element |
| `browser_select_option` | Select dropdown option |
| `browser_snapshot` | Get page accessibility snapshot |
| `browser_take_screenshot` | Screenshot (inline, not to disk) |
| `browser_evaluate` | Run JS on page |
| `browser_run_code` | Run Playwright code snippet |
| `browser_wait_for` | Wait for condition |
| `browser_tabs` | List open tabs |
| `browser_close` | Close current page |
| `browser_console_messages` | Get console output |
| `browser_network_requests` | Get network requests |
| `browser_navigate_back` | Go back |
| `browser_resize` | Resize viewport |
| `browser_drag` | Drag element |
| `browser_file_upload` | Upload file |
| `browser_handle_dialog` | Handle alert/confirm dialog |

Tools must be loaded via `ToolSearch` before first use:

```
ToolSearch: select:mcp__plugin_playwright_playwright__browser_navigate
```

### MCP Plugin Limitations

- **Cannot bypass proxy** — VPN hosts will get 502 errors
- **Screenshots are inline only** — cannot save to disk (use `browser_run_code` workaround)
- **Single page context** — hard to manage multiple tabs/contexts
- **No browser launch options** — cannot set proxy, user agent, viewport at launch time

### MCP Plugin + Standalone Hybrid

For advanced workflows, use MCP tools to interact with elements on public pages, but
switch to standalone scripts when you need to:
- Access VPN hosts
- Save screenshots to disk
- Control browser launch options
- Run complex multi-step flows

---

## TTT Environment Reference

| Env | URL | Status |
|---|---|---|
| QA-1 | `https://ttt-qa-1.noveogroup.com` | Primary test environment |
| QA-2 | `https://ttt-qa-2.noveogroup.com` | Secondary (may be down) |

Config file: `config/ttt/ttt.yml`

CAS logout URL: `https://cas-demo.noveogroup.com/logout`

---

## Output Directory

Save all Playwright artifacts to:
```
artifacts/playwright/
```

Use descriptive filenames:
```
artifacts/playwright/<user>-<page>-<date>.png
```

Example: `atushov-vacations-2026-02-27.png`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| 502 Bad Gateway on VPN host | Browser using HTTP_PROXY | Use standalone script with `delete process.env.HTTP_PROXY` |
| `ERR_MODULE_NOT_FOUND: playwright` | Not installed locally | `npm install --no-save playwright` |
| Login doesn't work (stays on login page) | Wrong selectors | Use `#username` for input, `button[type="submit"]` for button |
| Language switch doesn't work | EN already active or selector mismatch | Check if nav shows "RU" or "EN" first |
| Page content not loaded | SPA async loading | Add `page.waitForTimeout(2000)` or `waitForSelector` |
| MCP tool not found | Not loaded yet | Use `ToolSearch: select:mcp__plugin_playwright_playwright__<tool>` |
| Screenshot is blank/login page | Session lost on navigation | Ensure cookies persist (use same context) |
| `channel: 'chrome'` fails | Chrome not installed | Check `which google-chrome` — fallback to `chromium` |
