import { test, expect } from '@playwright/test';
import { adminToken, auth, createProject, uniquePep, openApp } from './helpers.js';

// End-to-end journeys found by the cycle 3 audit.
test.describe('Journeys: first login', () => {
  test('a temporary password forces a change before the app loads', async ({ page, request }) => {
    const token = await adminToken(request);
    const username = `t${Math.random().toString(36).slice(2, 9)}`;
    const temp = 'Temp#Passw0rd1';
    const res = await request.post('/api/users', { headers: auth(token), data: { username, password: temp, role: 'user' } });
    expect(res.ok()).toBeTruthy();
    // A password that an administrator sets for another user is temporary.
    const reset = await request.patch(`/api/users/${(await res.json()).id}/password`, { headers: auth(token), data: { new_password: temp } });
    expect(reset.ok()).toBeTruthy();

    const bad = [];
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('/api/token')) bad.push(`${r.status()} ${r.url()}`); });
    await page.addInitScript(() => localStorage.setItem('pmas_lang', 'en'));
    await page.goto('/frontend/index.html');
    await page.locator('#loginUsername').fill(username);
    await page.locator('#loginPassword').fill(temp);
    await page.locator('#loginForm button[type="submit"]').click();

    // Only the new-password step shows. The app does not load and sends no request that fails.
    await expect(page.locator('#forcePwdForm')).toBeVisible();
    await expect(page.locator('#appShell')).toBeHidden();
    await page.locator('#forcePwdNew').fill('Fresh#Passw0rd2');
    await page.locator('#forcePwdConfirm').fill('Other#Passw0rd3');
    await page.locator('#forcePwdForm button[type="submit"]').click();
    await expect(page.locator('#forcePwdError')).not.toHaveText('');
    await page.locator('#forcePwdConfirm').fill('Fresh#Passw0rd2');
    await page.locator('#forcePwdForm button[type="submit"]').click();

    await expect(page.locator('#loginForm')).toBeVisible();
    await expect(page.locator('#loginError')).not.toHaveText('');
    await page.locator('#loginUsername').fill(username);
    await page.locator('#loginPassword').fill('Fresh#Passw0rd2');
    await page.locator('#loginForm button[type="submit"]').click();
    await expect(page.locator('#appShell')).toBeVisible();
    await page.waitForLoadState('networkidle');
    expect(bad).toEqual([]);
    expect(errors).toEqual([]);
  });
});

test.describe('Journeys: failures and double clicks', () => {
  test('a failed list request shows the error and does not stay on Loading', async ({ page, request }) => {
    const token = await adminToken(request);
    await openApp(page, token);
    const pattern = /\/api\/(projects|cycles)(\?.*)?$/;
    await page.route(pattern, route => route.fulfill({ status: 500, contentType: 'text/plain', body: 'Internal Server Error' }));
    await page.locator('.tab-btn[data-tab="cycles"]').click();
    await expect(page.locator('#cyclesBody')).not.toContainText('Loading');
    await expect(page.locator('#cyclesBody')).toContainText(/error/i);
    await page.locator('.tab-btn[data-tab="projects"]').click();
    await expect(page.locator('#projectsBody')).not.toContainText('Loading');
    await page.unroute(pattern);
  });

  test('a double click on Save creates one cycle and one baseline', async ({ page, request }) => {
    const token = await adminToken(request);
    const name = `Dbl ${Math.random().toString(36).slice(2, 7)}`;
    const project = await createProject(request, token, uniquePep());
    await openApp(page, token);
    await page.locator('.tab-btn[data-tab="cycles"]').click();
    await page.locator('#newCycleBtn').click();
    await page.locator('#cycleNameInput').fill(name);
    await page.locator('#cycleStartInput').fill('2031-01-01');
    await page.locator('#cycleEndInput').fill('2031-01-31');
    await page.locator('#cycleSaveBtn').dblclick();
    await expect(page.locator('#cycleModal')).toBeHidden();
    const cycles = await (await request.get('/api/cycles', { headers: auth(token) })).json();
    expect(cycles.filter(c => c.name === name)).toHaveLength(1);

    await page.locator('.tab-btn[data-tab="projects"]').click();
    await page.waitForFunction(id => typeof _openBaselineModal === 'function' && _allProjects.some(p => p.id === id), project.id);
    await page.evaluate(id => _openBaselineModal(id), project.id);
    await page.locator('#baselineLabelInput').fill('Twice');
    await page.locator('#baselineModalBody button.btn-primary').dblclick();
    await expect(page.locator('.baseline-info-box.active')).toBeVisible();
    const baselines = await (await request.get(`/api/projects/${project.id}/baselines`, { headers: auth(token) })).json();
    expect(baselines).toHaveLength(1);
  });
});
