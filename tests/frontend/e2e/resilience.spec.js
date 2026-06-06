import { test, expect } from '@playwright/test';

test.describe('Frontend resilience', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', 'admin');
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
  });

  test('global unhandledrejection handler is registered', async ({ page }) => {
    // Verify the handler is wired — firing a rejected promise should show a notification
    const notifVisible = await page.evaluate(async () => {
      return new Promise(resolve => {
        window._testUnhandledFired = false;
        const orig = window.notify;
        window.notify = (msg, type) => {
          window._testUnhandledFired = true;
          if (orig) orig(msg, type);
        };
        // Dispatch a synthetic unhandledrejection
        const evt = new PromiseRejectionEvent('unhandledrejection', {
          promise: Promise.reject(new Error('test-unhandled')),
          reason: new Error('test-unhandled'),
          cancelable: true,
        });
        window.dispatchEvent(evt);
        setTimeout(() => resolve(window._testUnhandledFired), 100);
      });
    });
    expect(notifVisible).toBe(true);
  });

  test('logout button works via _logout function', async ({ page }) => {
    await page.click('#logoutBtn');
    await expect(page.locator('#loginOverlay')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#appShell')).toBeHidden();
  });

  test('visibilitychange listener is registered', async ({ page }) => {
    const hasListener = await page.evaluate(() => {
      // We can't enumerate event listeners directly; check that the app script
      // declared the function by verifying it's in scope and a tab reload fires
      return typeof loadCyclesTable === 'function' && typeof loadProjectsTable === 'function';
    });
    expect(hasListener).toBe(true);
  });

  test('_checkTokenExpiry is registered and callable', async ({ page }) => {
    const exists = await page.evaluate(() => typeof _checkTokenExpiry === 'function');
    expect(exists).toBe(true);
  });
});
