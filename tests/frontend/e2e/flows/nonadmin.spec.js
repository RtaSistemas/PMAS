import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, createUser, loginViaForm } from './helpers.js';

// A user with the role "user" must not see controls that always end in a 403 error.
test.describe('Flow: non-administrator user', () => {
  let token;
  let user;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
    await createProject(request, token, uniquePep());
    user = await createUser(request, token);
  });

  test('the Admin tab is hidden and the boot makes no forbidden request', async ({ page }) => {
    const seen = await loginViaForm(page, user.username, user.password);
    await expect(page.locator('#adminTabBtn')).toBeHidden();
    for (const tab of ['projects', 'cycles', 'team', 'my']) {
      await page.locator(`.tab-btn[data-tab="${tab}"]`).click();
      await page.waitForLoadState('networkidle');
    }
    expect(seen.forbidden).toEqual([]);
    expect(seen.errors).toEqual([]);
  });

  test('write controls are hidden for a non-administrator', async ({ page }) => {
    await loginViaForm(page, user.username, user.password);
    await page.locator('.tab-btn[data-tab="projects"]').click();
    await expect(page.locator('#projectsBody tr').first()).toBeVisible();
    await expect(page.locator('#newProjectBtn')).toBeHidden();
    await expect(page.locator('#importProjectsInput').locator('..')).toBeHidden();
    await expect(page.locator('#projectsBody button:text-is("Edit")')).toHaveCount(0);
    await expect(page.locator('#projectsBody .row-actions-item.danger')).toHaveCount(0);
    await page.locator('.tab-btn[data-tab="cycles"]').click();
    await expect(page.locator('#cyclesBody tr').first()).toBeVisible();
    await expect(page.locator('#newCycleBtn')).toBeHidden();
    await expect(page.locator('#cyclesBody button:text-is("Edit")')).toHaveCount(0);
    await expect(page.locator('#cyclesBody button:text-is("Delete")')).toHaveCount(0);
    await page.locator('.tab-btn[data-tab="team"]').click();
    for (const id of ['newSeniorityBtn', 'newRateCardBtn', 'saveConfigBtn', 'bulkSeniorityBtn']) {
      await expect(page.locator(`#${id}`), id).toBeHidden();
    }
    for (const id of ['importSeniorityInput', 'importRateCardInput']) {
      await expect(page.locator(`#${id}`).locator('..'), id).toBeHidden();
    }
  });

  test('a non-administrator changes the own password and signs in with the new one', async ({ page, request }) => {
    const own = await createUser(request, token);
    await loginViaForm(page, own.username, own.password);
    await page.locator('.tab-btn[data-tab="my"]').click();
    await page.locator('#myChangePwdBtn').click();
    await page.locator('#myCurrentPwdInput').fill(own.password);
    await page.locator('#myNewPwdInput').fill('Changed#Passw0rd2');
    await page.locator('#myPwdSaveBtn').click();
    await expect(page.locator('#myPwdModal')).toBeHidden();
    await expect(page.locator('#myPwdError')).toHaveText('');
    const ok = await request.post('/api/token', { form: { username: own.username, password: 'Changed#Passw0rd2' } });
    expect(ok.ok()).toBeTruthy();
    const old = await request.post('/api/token', { form: { username: own.username, password: own.password } });
    expect(old.ok()).toBeFalsy();
  });
});
