import { test, expect } from '@playwright/test';

// The checklist reads three list endpoints. The tests mock them, so the shared
// database and the admin password stay unchanged.
function mockCounts(page, { cycles = [], projects = [], uploads = [] }) {
  page.route('**/api/cycles', r => r.fulfill({ json: cycles }));
  page.route('**/api/projects', r => r.fulfill({ json: projects }));
  page.route('**/api/upload-history?limit=1', r => r.fulfill({ json: uploads }));
}

async function login(page) {
  await page.goto('/');
  await page.fill('#loginUsername', 'admin');
  await page.fill('#loginPassword', 'admin');
  await page.click('button[type="submit"]');
  await expect(page.locator('#appShell')).toBeVisible({ timeout: 10000 });
}

test.describe('First-use checklist', () => {
  test('shows 0 of 3 steps when the system has no data', async ({ page }) => {
    mockCounts(page, {});
    await login(page);
    const card = page.locator('#onboardingCard');
    await expect(card).toBeVisible();
    await expect(card.locator('.onboarding-progress')).toContainText('0');
    await expect(card.locator('.onboarding-step.todo')).toHaveCount(3);
  });

  test('marks finished steps and keeps a button for the open steps', async ({ page }) => {
    mockCounts(page, { cycles: [{ id: 1 }], projects: [{ id: 1 }] });
    await login(page);
    const card = page.locator('#onboardingCard');
    await expect(card.locator('.onboarding-step.done')).toHaveCount(2);
    await expect(card.locator('[data-onboard-step]')).toHaveCount(1);
  });

  test('hides the card when all 3 steps are complete', async ({ page }) => {
    mockCounts(page, { cycles: [{ id: 1 }], projects: [{ id: 1 }], uploads: [{ id: 1 }] });
    await login(page);
    await expect(page.locator('#onboardingCard')).toBeHidden();
  });

  test('the step button opens the matching tab', async ({ page }) => {
    mockCounts(page, {});
    await login(page);
    await page.locator('[data-onboard-step="0"]').click();
    await expect(page.locator('.tab-btn.active')).toHaveAttribute('data-tab', 'cycles');
  });
});
