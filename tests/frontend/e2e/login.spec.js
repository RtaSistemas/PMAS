import { test, expect } from '@playwright/test';

test.describe('Login page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('shows login overlay on first load', async ({ page }) => {
    await expect(page.locator('#loginOverlay')).toBeVisible();
    await expect(page.locator('#appShell')).toBeHidden();
  });

  test('shows PMAS brand text', async ({ page }) => {
    await expect(page.locator('.login-logo')).toContainText('PMAS');
  });

  test('shows username and password inputs', async ({ page }) => {
    await expect(page.locator('#loginUsername')).toBeVisible();
    await expect(page.locator('#loginPassword')).toBeVisible();
  });

  test('shows error message on invalid credentials', async ({ page }) => {
    await page.fill('#loginUsername', 'nonexistent');
    await page.fill('#loginPassword', 'wrongpassword');
    await page.click('button[type="submit"]');
    await expect(page.locator('#loginError')).not.toBeEmpty({ timeout: 5000 });
  });

  test('logs in successfully with admin credentials', async ({ page }) => {
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', 'admin');
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#loginOverlay')).toBeHidden();
  });
});

test.describe('App shell after login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', 'admin');
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
  });

  test('shows the main navigation tabs', async ({ page }) => {
    await expect(page.locator('.app-tabs')).toBeVisible();
    await expect(page.locator('.tab-btn').first()).toBeVisible();
  });

  test('shows Dashboard tab by default', async ({ page }) => {
    await expect(page.locator('#tab-dashboard')).not.toBeHidden();
  });

  test('shows logout button', async ({ page }) => {
    await expect(page.locator('#logoutBtn')).toBeVisible();
  });

  test('can switch to Projetos tab', async ({ page }) => {
    const projTab = page.locator('.tab-btn', { hasText: /Projetos/i });
    await projTab.click();
    await expect(page.locator('#tab-projects')).not.toBeHidden();
  });

  test('cycles section is visible inside Projetos tab', async ({ page }) => {
    // Ciclos live inside the Projetos tab, not a separate tab
    const projTab = page.locator('.tab-btn', { hasText: /Projetos/i });
    await projTab.click();
    await expect(page.locator('#tab-projects')).not.toBeHidden();
    await expect(page.locator('#cyclesTable')).toBeVisible();
  });

  test('admin tab is visible for admin user', async ({ page }) => {
    await expect(page.locator('#adminTabBtn')).toBeVisible();
  });

  test('logout returns to login screen', async ({ page }) => {
    await page.click('#logoutBtn');
    await expect(page.locator('#loginOverlay')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('#appShell')).toBeHidden();
  });
});
