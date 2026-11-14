import { test, expect } from '@playwright/test';
import { adminToken, auth, createProject, uniquePep, openApp } from './helpers.js';

test.describe('Flow: budget baseline', () => {
  test('an administrator locks a baseline for a project', async ({ page, request }) => {
    const token = await adminToken(request);
    const pep = uniquePep();
    const project = await createProject(request, token, pep);
    const errors = await openApp(page, token);

    await page.locator('.tab-btn[data-tab="projects"]').click();
    await page.waitForFunction(id => typeof _openBaselineModal === 'function'
      && _allProjects.some(p => p.id === id), project.id);
    await page.evaluate(id => _openBaselineModal(id), project.id);

    await expect(page.locator('#baselineModal')).toBeVisible();
    await expect(page.locator('.baseline-info-box.warning')).toBeVisible();   // no baseline yet

    const label = `Baseline ${pep}`;
    await page.locator('#baselineLabelInput').fill(label);
    await page.locator('#baselineModalBody button.btn-primary').click();

    await expect(page.locator('.baseline-info-box.active')).toContainText(label);
    const baselines = await (await request.get(`/api/projects/${project.id}/baselines`, { headers: auth(token) })).json();
    expect(baselines).toHaveLength(1);
    expect(baselines[0].is_active).toBe(true);
    expect(errors).toEqual([]);
  });
});
