import { test, expect } from '@playwright/test';
import { adminToken, auth, ensureCycle, createProject, uniquePep, timesheetCsv, openApp } from './helpers.js';

test.describe('Flow: timesheet import', () => {
  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
  });

  async function openUpload(page) {
    const errors = await openApp(page, token);
    await page.locator('.tab-btn[data-tab="my"]').click();
    await page.locator('[data-my-tab="upload"]').click();
    return errors;
  }

  test('imports a CSV file and lists it in the history', async ({ page, request }) => {
    const pep = uniquePep();
    await createProject(request, token, pep);
    const errors = await openUpload(page);

    const name = `import-${pep}.csv`;
    const csv = timesheetCsv(pep, [
      ['Ana Flow', '2026-01-05', 8],
      ['Ana Flow', '2026-01-06', 8],
      ['Caio Flow', '2026-01-05', 4],
    ]);
    await page.locator('#myAreaCsvInput').setInputFiles({ name, mimeType: 'text/csv', buffer: Buffer.from(csv) });

    await expect(page.locator('#myAreaUploadResult')).toContainText('3');
    await expect(page.locator('#ingestResultPanel')).toBeVisible();

    const history = await (await request.get('/api/upload-history', { headers: auth(token) })).json();
    const entry = history.find(h => h.source_file === name);
    expect(entry, 'the import is in the history').toBeTruthy();
    expect(entry.records_inserted).toBe(3);   // all rows reach a cycle; none goes to quarantine
    expect(entry.quarantine_added).toBe(0);
    await expect(page.locator('#myAreaUploadResult')).not.toContainText('⚠');
    expect(errors).toEqual([]);
  });

  test('shows an error for a file without the required columns', async ({ page }) => {
    const errors = await openUpload(page);
    await page.locator('#myAreaCsvInput').setInputFiles({
      name: 'wrong.csv', mimeType: 'text/csv', buffer: Buffer.from('Nome,Dia\nx,y\n'),
    });
    await expect(page.locator('#myAreaUploadResult')).toContainText(/Colunas obrigatórias|required/i);
    await expect(page.locator('#notification')).toBeVisible();
    expect(errors).toEqual([]);
  });
});
