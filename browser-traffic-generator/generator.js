/**
 * Browser Traffic Generator — Creates real Dynatrace RUM sessions
 * 
 * Uses Playwright (headless Chromium) to navigate the actual web UIs.
 * The browser executes the Dynatrace JS agent injected by OneAgent,
 * generating genuine user sessions with page actions, clicks, and XHR tracking.
 * 
 * Environment variables:
 *   APP_MODE        - "utility" or "retail" (required)
 *   APP_URL         - Base URL, e.g. https://utility.vptesttools.my
 *   CONCURRENT_USERS - Number of parallel browser sessions (default: 3)
 *   SESSION_INTERVAL - Seconds between new sessions per user slot (default: 60)
 *   NAVIGATIONS_PER_SESSION - Pages to visit before ending session (default: 10)
 */

const { chromium } = require('playwright');

const APP_MODE = process.env.APP_MODE || 'utility';
const APP_URL = process.env.APP_URL || (APP_MODE === 'utility'
  ? 'https://utility.vptesttools.my'
  : 'https://retail.vptesttools.my');
const CONCURRENT_USERS = parseInt(process.env.CONCURRENT_USERS || '3', 10);
const SESSION_INTERVAL = parseInt(process.env.SESSION_INTERVAL || '60', 10) * 1000;
const NAVIGATIONS = parseInt(process.env.NAVIGATIONS_PER_SESSION || '10', 10);

// ---- Utility app config ----
const UTILITY_USERS = [
  'operator_jones', 'engineer_chen', 'manager_smith', 'analyst_garcia',
  'dispatcher_lee', 'supervisor_patel', 'technician_wong', 'director_johnson',
  'operator_brown', 'engineer_martinez',
];
const UTILITY_SECTIONS = [
  'overview', 'scada', 'outages', 'metering', 'grid', 'reliability',
  'forecast', 'crew', 'notifications', 'weather', 'customers', 'pricing',
  'workorders', 'auditlog', 'alertcorrelation', 'health',
];

// ---- Retail app config ----
const RETAIL_USERS = [
  'admin_retail', 'mgr_gap', 'mgr_oldnavy', 'mgr_macys',
  'assoc_gap_1', 'assoc_gap_2', 'assoc_oldnavy_1', 'assoc_macys_1',
  'wh_east_1', 'wh_east_2',
];
// Tab indices in the retail Material UI tab bar (0-based)
const RETAIL_TAB_COUNT = 17;

// ---- Generic app config (env-driven) ----
const GENERIC_NAV_SELECTOR = process.env.NAV_SELECTOR || "nav a, [role='tab'], .nav button";
const GENERIC_LOGIN_USER_SELECTOR = process.env.LOGIN_USER_SELECTOR || '';
const GENERIC_LOGIN_PASS_SELECTOR = process.env.LOGIN_PASS_SELECTOR || '';
const GENERIC_LOGIN_SUBMIT_SELECTOR = process.env.LOGIN_SUBMIT_SELECTOR || '';
const GENERIC_LOGIN_USERNAME = process.env.LOGIN_USERNAME || '';
const GENERIC_LOGIN_PASSWORD = process.env.LOGIN_PASSWORD || '';
const GENERIC_LOGOUT_SELECTOR = process.env.LOGOUT_SELECTOR || '';

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function randomSleep(minS, maxS) {
  const ms = (minS + Math.random() * (maxS - minS)) * 1000;
  return sleep(ms);
}

// ---- Utility session ----
async function runUtilitySession(browser, slotId) {
  const username = pick(UTILITY_USERS);
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1920, height: 1080 },
    userAgent: pickUA(),
  });
  const page = await context.newPage();

  try {
    console.log(`[Slot ${slotId}] Utility session start — user: ${username}`);

    // 1. Navigate to app — triggers DT JS agent injection
    await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await randomSleep(2, 4);

    // 2. Login — fill username/password and submit
    // The login overlay has a select dropdown and input fields
    const loginOverlay = page.locator('#login-overlay');
    if (await loginOverlay.isVisible().catch(() => false)) {
      // Try the username select dropdown first
      const selectEl = page.locator('#login-user-select');
      if (await selectEl.isVisible().catch(() => false)) {
        await selectEl.selectOption(username);
        await randomSleep(0.5, 1);
      } else {
        // Fill manually
        await page.fill('#login-username', username);
        await page.fill('#login-password', 'utility2026');
      }
      await randomSleep(0.5, 1);
      await page.click('#login-submit');
      await randomSleep(2, 4);
    }

    // 3. Navigate through random sections
    for (let i = 0; i < NAVIGATIONS; i++) {
      const section = pick(UTILITY_SECTIONS);
      console.log(`[Slot ${slotId}]   nav ${i + 1}/${NAVIGATIONS}: #${section}`);

      // Click the nav button for this section
      const navButton = page.locator(`.nav button[data-section="${section}"]`);
      if (await navButton.isVisible().catch(() => false)) {
        await navButton.click();
      } else {
        // Fallback: use hash navigation
        await page.evaluate((s) => { window.location.hash = s; }, section);
      }

      // Wait for content to load (XHRs fire, DT tracks them)
      await page.waitForLoadState('networkidle').catch(() => {});
      await randomSleep(3, 8);

      // Simulate some scroll activity on every other page
      if (i % 2 === 0) {
        await page.evaluate(() => window.scrollBy(0, 300));
        await randomSleep(1, 2);
        await page.evaluate(() => window.scrollTo(0, 0));
      }
    }

    // 4. Logout
    const logoutBtn = page.locator('#logout-btn, button:has-text("Logout"), .logout-btn');
    if (await logoutBtn.first().isVisible().catch(() => false)) {
      await logoutBtn.first().click();
      await randomSleep(1, 2);
    }

    console.log(`[Slot ${slotId}] Utility session end — ${NAVIGATIONS} pages visited`);
  } catch (err) {
    console.error(`[Slot ${slotId}] Error:`, err.message);
  } finally {
    await context.close();
  }
}

// ---- Retail session ----
async function runRetailSession(browser, slotId) {
  const username = pick(RETAIL_USERS);
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1920, height: 1080 },
    userAgent: pickUA(),
  });
  const page = await context.newPage();

  try {
    console.log(`[Slot ${slotId}] Retail session start — user: ${username}`);

    // 1. Navigate to app — triggers DT JS agent injection
    await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await randomSleep(2, 4);

    // 2. Login — Material UI select dropdown + Login button
    // Wait for the login card to appear
    await page.waitForSelector('text=Select User', { timeout: 15000 }).catch(() => {});
    await randomSleep(1, 2);

    // Open the Material UI Select dropdown
    const selectDiv = page.locator('[role="combobox"], .MuiSelect-select, #mui-component-select-user');
    if (await selectDiv.first().isVisible().catch(() => false)) {
      await selectDiv.first().click();
      await randomSleep(0.5, 1);
      // Click the username option in the dropdown menu
      const option = page.locator(`[role="option"]:has-text("${username}"), li:has-text("${username}")`);
      if (await option.first().isVisible().catch(() => false)) {
        await option.first().click();
      } else {
        // Try direct selection via the listbox
        await page.locator(`[role="listbox"] >> text=${username}`).click().catch(() => {});
      }
      await randomSleep(0.5, 1);
    }

    // Click Login button
    const loginBtn = page.locator('button:has-text("Login")');
    if (await loginBtn.isVisible().catch(() => false)) {
      await loginBtn.click();
      await randomSleep(2, 4);
    }

    // 3. Navigate through random tabs
    for (let i = 0; i < NAVIGATIONS; i++) {
      const tabIndex = Math.floor(Math.random() * RETAIL_TAB_COUNT);
      console.log(`[Slot ${slotId}]   nav ${i + 1}/${NAVIGATIONS}: tab ${tabIndex}`);

      // Click the tab by role
      const tabs = page.locator('[role="tab"]');
      const tabCount = await tabs.count();
      if (tabIndex < tabCount) {
        await tabs.nth(tabIndex).click();
      }

      // Wait for API calls to complete
      await page.waitForLoadState('networkidle').catch(() => {});
      await randomSleep(3, 8);

      // Simulate scroll
      if (i % 2 === 0) {
        await page.evaluate(() => window.scrollBy(0, 300));
        await randomSleep(1, 2);
        await page.evaluate(() => window.scrollTo(0, 0));
      }
    }

    // 4. Logout
    const logoutBtn = page.locator('button:has-text("Logout")');
    if (await logoutBtn.isVisible().catch(() => false)) {
      await logoutBtn.click();
      await randomSleep(1, 2);
    }

    console.log(`[Slot ${slotId}] Retail session end — ${NAVIGATIONS} pages visited`);
  } catch (err) {
    console.error(`[Slot ${slotId}] Error:`, err.message);
  } finally {
    await context.close();
  }
}

// ---- Generic session (env-driven, works with any web app) ----
async function runGenericSession(browser, slotId) {
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1920, height: 1080 },
    userAgent: pickUA(),
  });
  const page = await context.newPage();

  try {
    console.log(`[Slot ${slotId}] Generic session start`);

    // 1. Navigate to app
    await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await randomSleep(2, 4);

    // 2. Login (if selectors provided)
    if (GENERIC_LOGIN_USER_SELECTOR && GENERIC_LOGIN_USERNAME) {
      await page.fill(GENERIC_LOGIN_USER_SELECTOR, GENERIC_LOGIN_USERNAME);
      if (GENERIC_LOGIN_PASS_SELECTOR && GENERIC_LOGIN_PASSWORD) {
        await page.fill(GENERIC_LOGIN_PASS_SELECTOR, GENERIC_LOGIN_PASSWORD);
      }
      await randomSleep(0.5, 1);
      if (GENERIC_LOGIN_SUBMIT_SELECTOR) {
        await page.click(GENERIC_LOGIN_SUBMIT_SELECTOR);
        await randomSleep(2, 4);
      }
    }

    // 3. Navigate through discoverable navigation elements
    for (let i = 0; i < NAVIGATIONS; i++) {
      const navItems = page.locator(GENERIC_NAV_SELECTOR);
      const count = await navItems.count();
      if (count === 0) {
        console.log(`[Slot ${slotId}]   No nav elements found, waiting...`);
        await randomSleep(3, 5);
        continue;
      }
      const idx = Math.floor(Math.random() * count);
      const label = await navItems.nth(idx).textContent().catch(() => `item-${idx}`);
      console.log(`[Slot ${slotId}]   nav ${i + 1}/${NAVIGATIONS}: "${(label || '').trim()}"`);

      await navItems.nth(idx).click().catch(() => {});
      await page.waitForLoadState('networkidle').catch(() => {});
      await randomSleep(3, 8);

      if (i % 2 === 0) {
        await page.evaluate(() => window.scrollBy(0, 300));
        await randomSleep(1, 2);
        await page.evaluate(() => window.scrollTo(0, 0));
      }
    }

    // 4. Logout (if selector provided)
    if (GENERIC_LOGOUT_SELECTOR) {
      const logoutBtn = page.locator(GENERIC_LOGOUT_SELECTOR);
      if (await logoutBtn.first().isVisible().catch(() => false)) {
        await logoutBtn.first().click();
        await randomSleep(1, 2);
      }
    }

    console.log(`[Slot ${slotId}] Generic session end — ${NAVIGATIONS} pages visited`);
  } catch (err) {
    console.error(`[Slot ${slotId}] Error:`, err.message);
  } finally {
    await context.close();
  }
}

// ---- User-Agent pool ----
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
];

function pickUA() {
  return pick(USER_AGENTS);
}

// ---- Session loop per slot ----
async function sessionLoop(browser, slotId) {
  const runSession = APP_MODE === 'utility' ? runUtilitySession
    : APP_MODE === 'retail' ? runRetailSession
    : runGenericSession;
  while (true) {
    await runSession(browser, slotId);
    const jitter = SESSION_INTERVAL * (0.5 + Math.random());
    console.log(`[Slot ${slotId}] Next session in ${Math.round(jitter / 1000)}s`);
    await sleep(jitter);
  }
}

// ---- Main ----
async function main() {
  console.log(`=== Browser Traffic Generator ===`);
  console.log(`Mode: ${APP_MODE} | URL: ${APP_URL}`);
  console.log(`Users: ${CONCURRENT_USERS} | Navs/session: ${NAVIGATIONS} | Interval: ${SESSION_INTERVAL / 1000}s`);
  console.log(`================================`);

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
  });

  console.log(`Browser launched (Chromium ${browser.version()})`);

  // Stagger session starts
  const slots = [];
  for (let i = 0; i < CONCURRENT_USERS; i++) {
    const delay = i * 5000; // 5s stagger between slots
    slots.push(
      sleep(delay).then(() => sessionLoop(browser, i + 1))
    );
  }

  await Promise.all(slots);
}

main().catch((err) => {
  console.error('Fatal:', err);
  process.exit(1);
});
