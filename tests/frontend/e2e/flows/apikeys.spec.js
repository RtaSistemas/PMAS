import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, timesheetCsv, openApp } from './helpers.js';

const upload = (request, key, name, csv) => request.post('/api/upload-timesheet', {
  headers: { 'X-API-Key': key },
  multipart: { file: { name, mimeType: 'text/csv', buffer: Buffer.from(csv, 'utf-8') } },
});

test.describe('Flow: API key for automatic import', () => {
  test('an administrator creates a key, a system imports with it, and the administrator revokes it', async ({ page, request }) => {
    const token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    const errors = await openApp(page, token);

    // Create the key in the Admin tab
    await page.locator('#adminTabBtn').click();
    await page.locator('#newApiKeyBtn').click();
    await expect(page.locator('#apiKeyModal')).toBeVisible();
    const name = `Importer ${pep}`;
    await page.locator('#apiKeyNameInput').fill(name);
    await page.locator('#apiKeySaveBtn').click();

    // The key is shown once
    await expect(page.locator('#apiKeyShownModal')).toBeVisible();
    const key = (await page.locator('#apiKeyValue').textContent()).trim();
    expect(key).toMatch(/^pmas_/);
    await page.locator('#apiKeyShownModal .btn-primary').click();

    const row = page.locator('#apiKeysBody tr', { hasText: name });
    await expect(row).toContainText(key.slice(0, 10));
    await expect(row).not.toContainText(key);             // the list never shows the full key
    await expect(row).toContainText('Active');

    // A system imports with the key. No login is needed.
    const csv = timesheetCsv(pep, [['Ivo Flow', '2026-01-05', 8], ['Ivo Flow', '2026-01-06', 8]]);
    const ok = await upload(request, key, `api-${pep}.csv`, csv);
    expect(ok.status()).toBe(200);
    expect((await ok.json()).records_inserted).toBe(2);

    // The key does not open any other route
    expect((await request.get('/api/cycles', { headers: { 'X-API-Key': key } })).status()).toBe(401);

    // Revoke in the UI
    await page.locator('#adminTabBtn').click();
    await row.locator('[data-revoke-key]').click();
    await page.locator('#confirmModalOk').click();
    await expect(row).toContainText('Revoked');

    const denied = await upload(request, key, `api2-${pep}.csv`, csv);
    expect(denied.status()).toBe(401);
    expect(errors).toEqual([]);
  });

  test('the form asks for a name of at least 3 characters', async ({ page, request }) => {
    const token = await adminToken(request);
    await openApp(page, token);
    await page.locator('#adminTabBtn').click();
    await page.locator('#newApiKeyBtn').click();
    await page.locator('#apiKeyNameInput').fill('ab');
    await page.locator('#apiKeySaveBtn').click();
    await expect(page.locator('#apiKeyError')).toContainText('3 characters');
    await expect(page.locator('#apiKeyShownModal')).toBeHidden();
  });
});
