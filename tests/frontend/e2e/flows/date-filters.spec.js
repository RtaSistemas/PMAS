import { test, expect } from '@playwright/test';
import { adminToken, auth, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

// A range that cuts through the middle of the cycle E2E Jan 2026 (01-01 to 01-31).
const RANGE = { date_from: '2026-01-10', date_to: '2026-01-31' };

async function seed(request, token) {
  await ensureCycle(request, token);
  const pep = uniquePep();
  await createProject(request, token, pep);
  const s = await uploadViaApi(request, token, `d-${pep}.csv`, timesheetCsv(pep, [
    ['Dora Date', '2026-01-05', 8], ['Dora Date', '2026-01-12', 6], ['Evan Date', '2026-01-20', 4],
  ]));
  expect(s.records_inserted).toBe(3);
  return pep;
}

test.describe('Flow: date filters', () => {
  test('the forecast note shows only when a date filter is set', async ({ page, request }) => {
    const token = await adminToken(request);
    const pep = await seed(request, token);
    const errors = await openApp(page, token);
    await page.locator('.atab-btn[data-atab="forecast"]').click();
    await page.locator('#forecastPepSelect').selectOption(pep);
    await expect(page.locator('#forecastKpis')).toBeVisible();
    await expect(page.locator('#forecastDateNote')).toBeHidden();

    await page.locator('#dateFromInput').fill('2026-01-10');
    await page.locator('#dateFromInput').dispatchEvent('change');
    await expect(page.locator('#forecastDateNote')).toBeVisible();
    await expect(page.locator('#forecastDateNote')).toContainText('The forecast covers the whole project');

    await page.locator('#dateFromInput').fill('');
    await page.locator('#dateFromInput').dispatchEvent('change');
    await expect(page.locator('#forecastDateNote')).toBeHidden();
    expect(errors).toEqual([]);
  });

  test('the date filter does not change the forecast numbers', async ({ page, request }) => {
    const token = await adminToken(request);
    const pep = await seed(request, token);
    const errors = await openApp(page, token);
    await page.locator('.atab-btn[data-atab="forecast"]').click();
    await page.locator('#forecastPepSelect').selectOption(pep);
    await expect(page.locator('#forecastKpis')).toBeVisible();
    const before = await page.locator('#forecastKpis').innerText();

    await page.locator('#dateFromInput').fill(RANGE.date_from);
    await page.locator('#dateToInput').fill(RANGE.date_to);
    await page.locator('#loadBtn').click();
    await expect(page.locator('#forecastDateNote')).toBeVisible();
    await expect(page.locator('#forecastKpis')).toBeVisible();
    expect(await page.locator('#forecastKpis').innerText()).toBe(before);

    // The same holds at the API level.
    const base = await (await request.get(`/api/v2/forecast?pep_wbs=${pep}`, { headers: auth(token) })).json();
    const filt = await (await request.get(
      `/api/v2/forecast?pep_wbs=${pep}&date_from=${RANGE.date_from}&date_to=${RANGE.date_to}`,
      { headers: auth(token) })).json();
    expect(filt).toEqual(base);
    expect(errors).toEqual([]);
  });

  test('portfolio, effort and trends totals agree for a range inside a cycle', async ({ request }) => {
    const token = await adminToken(request);
    const pep = await seed(request, token);
    const q = `date_from=${RANGE.date_from}&date_to=${RANGE.date_to}`;
    const get = async path => (await request.get(`${path}${q}`, { headers: auth(token) })).json();
    const portfolio = await get(`/api/v2/portfolio?pep_wbs=${pep}&`);
    const effort = await get(`/api/v2/effort?pep_wbs=${pep}&`);
    const trends = await get(`/api/v2/trends?pep_wbs=${pep}&`);
    const sum = (rows, k) => rows.reduce((a, r) => a + r[k], 0);
    expect(sum(portfolio, 'total_hours')).toBe(10);          // 6 + 4: 01-05 is outside the range
    expect(sum(effort, 'total_hours')).toBe(10);
    expect(sum(trends, 'total_hours')).toBe(10);
  });
});
