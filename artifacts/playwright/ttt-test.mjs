import { chromium } from 'playwright';

// Unset proxy env vars so Chromium connects directly to VPN hosts
delete process.env.HTTP_PROXY;
delete process.env.HTTPS_PROXY;
delete process.env.http_proxy;
delete process.env.https_proxy;

const BASE_URL = 'https://ttt-qa-1.noveogroup.com';
const SCREENSHOT_DIR = '/home/v/Dev/ttt-expert-v1/artifacts/playwright';

(async () => {
  const browser = await chromium.launch({
    headless: true,
    channel: 'chrome'
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true
  });

  const page = await context.newPage();

  try {
    // Step 1: Navigate to main page
    console.log('Step 1: Navigating to TTT QA-1...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    console.log(`  URL: ${page.url()}`);
    console.log(`  Title: ${await page.title()}`);

    // Step 2: Login as pvaynmaster (login-only auth, no password)
    console.log('Step 2: Logging in as pvaynmaster...');
    await page.fill('#username', 'pvaynmaster');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle', timeout: 30000 }),
      page.click('button[type="submit"]')
    ]);
    console.log(`  Logged in. URL: ${page.url()}`);

    // Step 3: Switch to English
    console.log('Step 3: Switching to English...');
    // The nav bar has "RU" with a dropdown chevron — click it to open language menu
    const ruDropdown = page.locator('text=RU').first();
    await ruDropdown.click();
    await page.waitForTimeout(500);

    // Screenshot dropdown to see options
    await page.screenshot({ path: `${SCREENSHOT_DIR}/debug-lang-dropdown.png` });

    // Look for EN option in the dropdown
    const enOption = page.locator('text=EN').first();
    if (await enOption.isVisible({ timeout: 3000 }).catch(() => false)) {
      await enOption.click();
      await page.waitForLoadState('networkidle', { timeout: 15000 });
      console.log('  Switched to English');
    } else {
      // Maybe it's a direct link, try other patterns
      console.log('  EN option not visible after clicking RU, dumping dropdown state...');
      const dropdownHtml = await page.evaluate(() => {
        // Look for any visible dropdown/popover
        const menus = document.querySelectorAll('[class*="dropdown"], [class*="menu"], [class*="popover"], [role="menu"], [role="listbox"]');
        return Array.from(menus).map(m => m.outerHTML.substring(0, 300)).join('\n---\n');
      });
      console.log(`  Dropdown HTML: ${dropdownHtml.substring(0, 500)}`);
    }

    await page.screenshot({ path: `${SCREENSHOT_DIR}/debug-after-lang-switch.png` });
    console.log(`  Current URL: ${page.url()}`);

    // Step 4: Navigate to My Vacations page
    console.log('Step 4: Navigating to My Vacations page...');
    // The menu item is "Календарь отсутствий" (RU) / "Absence calendar" (EN) with a dropdown
    // Let's hover/click on it to see submenu options
    const absenceMenu = page.locator('a:has-text("Absence"), a:has-text("Calendar"), a:has-text("Календарь")').first();
    if (await absenceMenu.isVisible({ timeout: 3000 }).catch(() => false)) {
      await absenceMenu.click();
      await page.waitForTimeout(500);
    }

    // Try direct URL to "my vacations" page
    await page.goto(`${BASE_URL}/vacation/my`, { waitUntil: 'networkidle', timeout: 30000 });
    let currentUrl = page.url();
    console.log(`  After /vacation/my: ${currentUrl}`);

    // If that didn't work, try other vacation URLs
    if (currentUrl.includes('login') || currentUrl === BASE_URL + '/') {
      await page.goto(`${BASE_URL}/vacation`, { waitUntil: 'networkidle', timeout: 30000 });
      currentUrl = page.url();
      console.log(`  After /vacation: ${currentUrl}`);
    }

    // Wait a moment for any dynamic content to load
    await page.waitForTimeout(2000);

    // Step 5: Take screenshot
    console.log('Step 5: Taking screenshot...');
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/vacations-page.png`,
      fullPage: true
    });
    console.log('  Screenshot saved to artifacts/playwright/vacations-page.png');

    // Step 6: Logout
    console.log('Step 6: Logging out...');
    await page.goto('https://cas-demo.noveogroup.com/logout', { waitUntil: 'networkidle', timeout: 30000 });
    const logoutText = await page.textContent('body');
    if (logoutText.toLowerCase().includes('logout')) {
      console.log('  Logout successful');
    } else {
      console.log(`  Logout page: ${page.url()}`);
    }

    console.log('\nAll steps completed successfully!');
  } catch (error) {
    console.error(`Error: ${error.message}`);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/error-screenshot.png`, fullPage: true });
    console.log('Error screenshot saved.');
  } finally {
    await browser.close();
  }
})();
