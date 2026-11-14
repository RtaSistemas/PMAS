import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

test.describe('Flow: forecast', () => {
  test('selecting a PEP shows the EVM indicators and the chart', async ({ page, request }) => {
    const token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    const summary = await uploadViaApi(request, token, `f-${pep}.csv`, timesheetCsv(pep, [
      ['Fabio Flow', '2026-01-05', 8], ['Fabio Flow', '2026-01-06', 8], ['Gina Flow', '2026-01-07', 6],
    ]));
    expect(summary.records_inserted).toBe(3);

    const errors = await openApp(page, token);
    await page.locator('.atab-btn[data-atab="forecast"]').click();
    await expect(page.locator('#forecastPepSelect option[value="' + pep + '"]')).toHaveCount(1);
    await page.locator('#forecastPepSelect').selectOption(pep);

    await expect(page.locator('#forecastKpis')).toBeVisible();
    await expect(page.locator('#forecastKpis')).toContainText(/CPI/);
    await expect(page.locator('#forecastChart canvas, #forecastChart svg').first()).toBeVisible();
    expect(errors).toEqual([]);
  });
});
