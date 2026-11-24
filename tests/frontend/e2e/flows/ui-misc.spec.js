import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

test.describe('Flow: interface details', () => {
  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    await uploadViaApi(request, token, `ui-${pep}.csv`, timesheetCsv(pep, [['Ugo Ui', '2026-01-09', 5]]));
  });

  test('the active filter count goes away after Clear', async ({ page }) => {
    await openApp(page, token);
    await page.locator('#dateFromInput').fill('2026-01-01');
    await expect(page.locator('#filterActiveCount')).toBeVisible();
    await page.locator('#clearBtn').click();
    await expect(page.locator('#filterActiveCount')).toBeHidden();
  });

  test('Escape closes a filter panel after a mouse click, and the panel does not cover Load', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openApp(page, token);
    await page.locator('#cycleMs-toggle').click();
    await expect(page.locator('#cycleMs .ms-dropdown')).toBeVisible();
    const covered = await page.evaluate(() => {
      const r = document.getElementById('loadBtn').getBoundingClientRect();
      const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return !top.closest('#loadBtn');
    });
    expect(covered, 'the open panel covers the Load button').toBe(false);
    await page.locator('#cycleMs .ms-option').nth(1).click();   // a mouse click builds the panel again
    await page.keyboard.press('Escape');
    await expect(page.locator('#cycleMs .ms-dropdown')).toBeHidden();
  });

  test('the page loads no missing file and has a favicon', async ({ page }) => {
    const missing = [];
    page.on('response', r => { if (r.status() === 404) missing.push(r.url()); });
    await openApp(page, token);
    await page.waitForLoadState('networkidle');
    expect(missing).toEqual([]);
    await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', /^data:image\/svg\+xml/);
  });

  test('dates in the tables use dd/mm/yyyy', async ({ page }) => {
    await openApp(page, token);
    await page.locator('.tab-btn[data-tab="cycles"]').click();
    await expect(page.locator('#cyclesBody')).toContainText('01/01/2026');
    await expect(page.locator('#cyclesBody')).toContainText('31/01/2026');
  });

  test('a chart has a clean label, without NaN', async ({ page }) => {
    await openApp(page, token);
    await page.locator('#loadBtn').click();
    await page.waitForFunction(() => !!echarts.getInstanceByDom(document.getElementById('effortChart')));
    const label = await page.locator('#effortChart').getAttribute('aria-label');
    expect(label).toBeTruthy();
    expect(label).not.toMatch(/NaN|The chart is/);
  });

  test('the date filters have labels and index.html has no inline style', async ({ page, request }) => {
    await openApp(page, token);
    await expect(page.locator('label[for="dateFromInput"]')).toHaveCount(1);
    await expect(page.locator('label[for="dateToInput"]')).toHaveCount(1);
    const html = await (await request.get('/frontend/index.html')).text();
    expect(html.match(/\sstyle="/g)).toBeNull();
  });

  test('Escape closes only the top modal', async ({ page }) => {
    await openApp(page, token);
    await page.evaluate(() => { openModal('cycleModal'); openModal('confirmModal'); });
    await expect(page.locator('#confirmModal')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#confirmModal')).toBeHidden();
    await expect(page.locator('#cycleModal')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#cycleModal')).toBeHidden();
  });

  test('a cancelled confirm dialog does not run its action later', async ({ page }) => {
    await openApp(page, token);
    await page.evaluate(() => {
      window.__calls = [];
      confirmDialog('first', () => window.__calls.push('first'));
    });
    await page.keyboard.press('Escape');
    await page.evaluate(() => confirmDialog('second', () => window.__calls.push('second')));
    await page.locator('#confirmModalOk').click();
    expect(await page.evaluate(() => window.__calls)).toEqual(['second']);
  });
});
