/**
 * TTT Playwright Template — Standalone browser automation script
 *
 * Usage:
 *   node .claude/skills/playwright-browser/scripts/ttt-template.mjs [options]
 *
 * Options:
 *   --user <login>       TTT login (default: atushov)
 *   --env <env>          Environment: qa-1 or qa-2 (default: qa-1)
 *   --lang <lang>        Language: en or ru (default: en)
 *   --page <path>        Page to navigate to after login (default: /report)
 *   --screenshot <path>  Screenshot output path (default: artifacts/playwright/screenshot.png)
 *   --no-logout          Skip logout step
 *   --viewport <WxH>     Viewport size (default: 1440x900)
 *
 * Prerequisites:
 *   npm install --no-save playwright
 *
 * Example:
 *   node .claude/skills/playwright-browser/scripts/ttt-template.mjs \
 *     --user pvaynmaster --page /vacation/my --screenshot artifacts/playwright/vacations.png
 */

import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'fs';
import { dirname } from 'path';

// ── Proxy bypass (CRITICAL for VPN hosts) ──────────────────────────────
delete process.env.HTTP_PROXY;
delete process.env.HTTPS_PROXY;
delete process.env.http_proxy;
delete process.env.https_proxy;

// ── Parse CLI args ─────────────────────────────────────────────────────
function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = {
    user: 'atushov',
    env: 'qa-1',
    lang: 'en',
    page: '/report',
    screenshot: 'artifacts/playwright/screenshot.png',
    logout: true,
    viewport: { width: 1440, height: 900 }
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--user':      opts.user = args[++i]; break;
      case '--env':        opts.env = args[++i]; break;
      case '--lang':       opts.lang = args[++i]; break;
      case '--page':       opts.page = args[++i]; break;
      case '--screenshot': opts.screenshot = args[++i]; break;
      case '--no-logout':  opts.logout = false; break;
      case '--viewport': {
        const [w, h] = args[++i].split('x').map(Number);
        opts.viewport = { width: w, height: h };
        break;
      }
    }
  }

  opts.baseUrl = `https://ttt-${opts.env}.noveogroup.com`;
  return opts;
}

const opts = parseArgs(process.argv);

// ── Ensure output directory exists ─────────────────────────────────────
const screenshotDir = dirname(opts.screenshot);
if (!existsSync(screenshotDir)) {
  mkdirSync(screenshotDir, { recursive: true });
}

// ── Main ───────────────────────────────────────────────────────────────
(async () => {
  const browser = await chromium.launch({
    headless: true,
    channel: 'chrome'
  });

  const context = await browser.newContext({
    viewport: opts.viewport,
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    // Step 1: Navigate to main page
    console.log(`Step 1: Navigating to TTT ${opts.env}...`);
    await page.goto(opts.baseUrl, { waitUntil: 'networkidle', timeout: 30000 });
    console.log(`  URL: ${page.url()}`);

    // Step 2: Login
    console.log(`Step 2: Logging in as ${opts.user}...`);
    await page.fill('#username', opts.user);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
      page.click('button[type="submit"]')
    ]);
    console.log(`  Logged in. URL: ${page.url()}`);

    // Step 3: Switch language if needed
    const targetLang = opts.lang.toUpperCase();
    const otherLang = targetLang === 'EN' ? 'RU' : 'EN';
    console.log(`Step 3: Ensuring language is ${targetLang}...`);

    const langIndicator = page.locator(`nav >> text=/^${otherLang}$/`).first();
    if (await langIndicator.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Current language is the OTHER one, need to switch
      await langIndicator.click();
      await page.waitForTimeout(500);
      const targetOption = page.locator(`text=${targetLang}`).first();
      if (await targetOption.isVisible({ timeout: 3000 }).catch(() => false)) {
        await targetOption.click();
        await page.waitForLoadState('networkidle', { timeout: 15000 });
        console.log(`  Switched to ${targetLang}`);
      }
    } else {
      console.log(`  Already in ${targetLang}`);
    }

    // Step 4: Navigate to target page
    console.log(`Step 4: Navigating to ${opts.page}...`);
    await page.goto(`${opts.baseUrl}${opts.page}`, {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    // Wait for dynamic content
    await page.waitForTimeout(2000);
    console.log(`  URL: ${page.url()}`);

    // Step 5: Screenshot
    console.log('Step 5: Taking screenshot...');
    await page.screenshot({
      path: opts.screenshot,
      fullPage: true
    });
    console.log(`  Saved to ${opts.screenshot}`);

    // Step 6: Logout
    if (opts.logout) {
      console.log('Step 6: Logging out...');
      await page.goto('https://cas-demo.noveogroup.com/logout', {
        waitUntil: 'networkidle',
        timeout: 30000
      });
      const body = await page.textContent('body');
      console.log(body.toLowerCase().includes('logout') ? '  Logout successful' : `  Logout page: ${page.url()}`);
    } else {
      console.log('Step 6: Skipping logout (--no-logout)');
    }

    console.log('\nAll steps completed successfully!');
  } catch (error) {
    console.error(`Error: ${error.message}`);
    const errPath = opts.screenshot.replace(/\.png$/, '-error.png');
    await page.screenshot({ path: errPath, fullPage: true });
    console.log(`Error screenshot saved to ${errPath}`);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
