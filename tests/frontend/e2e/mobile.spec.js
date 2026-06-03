import { test, expect, devices } from '@playwright/test';

const mobile = devices['Pixel 5'];

test.describe('Mobile responsiveness', () => {
  test.use({ viewport: mobile.viewport, userAgent: mobile.userAgent });

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Login
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', 'admin');
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
  });

  test('header semaphore is hidden on mobile', async ({ page }) => {
    const sem = page.locator('#headerSemaphore');
    // Either hidden attribute or CSS display:none
    const isHidden = await sem.evaluate(el =>
      el.hidden || getComputedStyle(el).display === 'none' || getComputedStyle(el).visibility === 'hidden'
    );
    expect(isHidden).toBe(true);
  });

  test('nav tabs are scrollable on mobile', async ({ page }) => {
    const tabs = page.locator('.app-tabs');
    const overflowX = await tabs.evaluate(el => getComputedStyle(el).overflowX);
    expect(['auto', 'scroll']).toContain(overflowX);
  });

  test('page renders without horizontal overflow', async ({ page }) => {
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    // Allow small tolerance (scrollbar, etc.)
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20);
  });

  test('table-responsive containers allow horizontal scroll', async ({ page }) => {
    // Navigate to Projetos tab
    await page.locator('.tab-btn', { hasText: /Projetos/i }).click();
    const wrapper = page.locator('.table-responsive').first();
    const overflowX = await wrapper.evaluate(el => getComputedStyle(el).overflowX);
    expect(['auto', 'scroll']).toContain(overflowX);
  });
});
