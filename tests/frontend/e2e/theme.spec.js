import { test, expect } from '@playwright/test';

test.describe('Theme customization modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', 'admin');
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
    // Navigate to Admin tab
    await page.locator('#adminTabBtn').click();
    await expect(page.locator('#tab-admin')).not.toBeHidden();
  });

  test('opens theme modal when button is clicked', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#themeModal')).toBeVisible({ timeout: 3000 });
  });

  test('modal has 3 color columns', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#themeColStructure')).toBeVisible();
    await expect(page.locator('#themeColInteraction')).toBeVisible();
    await expect(page.locator('#themeColSemantic')).toBeVisible();
  });

  test('modal closes with cancel button', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#themeModal')).toBeVisible({ timeout: 3000 });
    await page.locator('#cancelThemeBtn').click();
    await expect(page.locator('#themeModal')).toBeHidden();
  });

  test('modal closes with X button', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#themeModal')).toBeVisible({ timeout: 3000 });
    await page.locator('#closeThemeModalBtn').click();
    await expect(page.locator('#themeModal')).toBeHidden();
  });

  test('color fields are present for all 3 columns', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#themeColorTxt_color_background')).toBeVisible();
    await expect(page.locator('#themeColorTxt_color_primary')).toBeVisible();
    await expect(page.locator('#themeColorTxt_color_success')).toBeVisible();
  });

  test('palette has 8 color inputs', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    const palItems = page.locator('#themeModalPalette .theme-pal-item');
    await expect(palItems).toHaveCount(8);
  });

  test('density buttons are present', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('.theme-density-btn[data-density="normal"]')).toBeVisible();
    await expect(page.locator('.theme-density-btn[data-density="compact"]')).toBeVisible();
  });

  test('border radius buttons are present', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('.theme-radius-btn[data-radius="sharp"]')).toBeVisible();
    await expect(page.locator('.theme-radius-btn[data-radius="rounded"]')).toBeVisible();
  });

  test('restore defaults button is visible in modal', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#restoreDefaultThemeBtn')).toBeVisible();
  });

  test('save theme button is visible in modal', async ({ page }) => {
    await page.locator('#openThemeModalBtn').click();
    await expect(page.locator('#saveThemeBtn')).toBeVisible();
  });
});
