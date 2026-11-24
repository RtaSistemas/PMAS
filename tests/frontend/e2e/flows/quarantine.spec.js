import { test, expect } from '@playwright/test';
import { adminToken, auth, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

// A row with more than 24 hours in one day breaks the system rule and goes to quarantine.
test.describe('Flow: quarantine review', () => {
  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
  });

  async function quarantineRecord(request, who) {
    const pep = uniquePep();
    await createProject(request, token, pep);
    const summary = await uploadViaApi(request, token, `q-${pep}.csv`,
      timesheetCsv(pep, [[who, '2026-01-07', 30]]));
    expect(summary.quarantine_records_added).toBe(1);
    const pending = await (await request.get('/api/quarantine?review_status=pending', { headers: auth(token) })).json();
    const record = pending.find(r => r.raw_data?.Colaborador === who);
    expect(record, 'the row is in quarantine').toBeTruthy();
    return record;
  }

  async function review(page, request, who, button, expected) {
    const record = await quarantineRecord(request, who);
    const errors = await openApp(page, token);
    await page.locator('.tab-btn[data-tab="my"]').click();
    await page.locator('[data-my-tab="upload"]').click();   // the quarantine list is in this sub-tab
    await page.waitForFunction(() => typeof _openQRDetail === 'function' && Array.isArray(_qrCache) && _qrCache.length > 0);
    await page.evaluate(id => _openQRDetail(id), record.id);
    await expect(page.locator('#qrDetailModal')).toBeVisible();
    await expect(page.locator('#qrDCollab')).toHaveText(who);
    await page.locator(button).click();
    await expect.poll(async () => {
      const r = await (await request.get(`/api/quarantine/${record.id}`, { headers: auth(token) })).json();
      return r.review_status;
    }).toBe(expected);
    expect(errors).toEqual([]);
  }

  test('an administrator rejects a quarantined row', async ({ page, request }) => {
    await review(page, request, 'Dora Flow', '#qrRejectBtn', 'rejected');
  });

  test('an administrator approves a quarantined row', async ({ page, request }) => {
    await review(page, request, 'Eli Flow', '#qrApproveBtn', 'approved');
  });
});
