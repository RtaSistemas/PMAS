import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

test.describe('Flow: printed report', () => {
  test('the printed report has a header with the report name, the date, the user and the active filters', async ({ page, request }) => {
    const token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    await uploadViaApi(request, token, `p-${pep}.csv`, timesheetCsv(pep, [['Hugo Flow', '2026-01-05', 8]]));

    const errors = await openApp(page, token);
    await page.waitForFunction(() => cycleMs.items.length > 0 && pepMs.items.length > 0);
    await page.evaluate(code => { pepMs.selectOnly(code); }, pep);
    await page.locator('#dateFromInput').fill('2026-01-01');

    // The header is hidden on screen
    await expect(page.locator('#printHeader')).toBeHidden();

    await page.emulateMedia({ media: 'print' });
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));

    const header = page.locator('#printHeader');
    await expect(header).toBeVisible();
    await expect(header.locator('.print-title')).toContainText('Dashboard');
    await expect(header.locator('.print-generated')).toContainText('admin');
    await expect(header.locator('.print-filters')).toContainText(pep);
    await expect(header.locator('.print-filters')).toContainText('01/01/2026');
    // The navigation and the onboarding card do not print
    await expect(page.locator('.app-tabs')).toBeHidden();
    await expect(page.locator('#onboardingCard')).toBeHidden();
    expect(errors).toEqual([]);
  });

  test('the header says that no filter is active when the filters are empty', async ({ page, request }) => {
    const token = await adminToken(request);
    await openApp(page, token);
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await expect(page.locator('#printHeader .print-filters')).toContainText('No filter is active');
  });
});
