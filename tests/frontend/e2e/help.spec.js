import { test, expect } from '@playwright/test';
import { adminPassword } from './admin-password.js';

test.describe('Help page', () => {
  test('the header has a Help link that opens the help page', async ({ page, context }) => {
    await page.goto('/');
    await page.fill('#loginUsername', 'admin');
    await page.fill('#loginPassword', await adminPassword(page));
    await page.click('button[type="submit"]');
    await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });

    const link = page.locator('#helpBtn');
    await expect(link).toBeVisible();
    const [popup] = await Promise.all([context.waitForEvent('page'), link.click()]);
    await expect(popup).toHaveURL(/\/frontend\/help\.html$/);
    await expect(popup.locator('h1:visible')).toHaveCount(1);
  });

  test('the help page switches between English and Portuguese', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('pmas_lang', 'en'));
    await page.goto('/frontend/help.html');
    await expect(page.locator('h1:visible')).toHaveText('PMAS Help');
    await page.click('#helpLangBtn');
    await expect(page.locator('h1:visible')).toHaveText('Ajuda do PMAS');
  });

  test('the help page lists the required import columns', async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('pmas_lang', 'en'));
    await page.goto('/frontend/help.html');
    for (const col of ['Colaborador', 'Data', 'Horas totais (decimal)']) {
      await expect(page.locator('article:visible code', { hasText: col }).first()).toBeVisible();
    }
  });
});

test('the help page shows one back link at a time', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('pmas_lang', 'en'));
  await page.goto('/frontend/help.html');
  await expect(page.locator('.help-bar a:visible')).toHaveCount(1);
});
