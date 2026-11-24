import { test, expect } from '@playwright/test';
import { adminToken, openApp } from './helpers.js';

// The forms must stop bad input in the browser. They must not rely on the server for the first check.
test.describe('Flow: client-side validation', () => {
  let token;
  test.beforeAll(async ({ request }) => { token = await adminToken(request); });

  /** Count the write requests that the page sends. */
  function trackWrites(page) {
    const writes = [];
    page.on('request', r => { if (['POST', 'PUT', 'PATCH'].includes(r.method())) writes.push(`${r.method()} ${new URL(r.url()).pathname}`); });
    return writes;
  }

  test('the project form checks the PEP code and the dates', async ({ page }) => {
    const errors = await openApp(page, token);
    const writes = trackWrites(page);
    await page.locator('.tab-btn[data-tab="projects"]').click();
    await page.locator('#newProjectBtn').click();
    await page.locator('#projectPepInput').fill('NOT A PEP');
    await page.locator('#projectSaveBtn').click();
    await expect(page.locator('#projectError')).toContainText('PEP code must have');
    await page.locator('#projectPepInput').fill('VAL-12345');
    await page.locator('#projectStartInput').fill('2026-06-01');
    await page.locator('#projectPlannedEndInput').fill('2026-01-01');
    await page.locator('#projectSaveBtn').click();
    await expect(page.locator('#projectError')).toContainText('planned end date');
    expect(writes.filter(w => w.includes('/api/projects'))).toEqual([]);
    expect(errors).toEqual([]);
  });

  test('the Team form needs a warning threshold below the critical threshold', async ({ page }) => {
    await openApp(page, token);
    const writes = trackWrites(page);
    await page.locator('.tab-btn[data-tab="team"]').click();
    await page.locator('#budgetWarningInput').fill('0.95');
    await page.locator('#budgetCriticalInput').fill('0.9');
    await page.locator('#saveConfigBtn').click();
    await expect(page.locator('#configMsg')).toContainText('lower than the critical');
    expect(writes.filter(w => w.includes('/api/config'))).toEqual([]);
  });

  test('a validation rule with a comparison operator needs a value', async ({ page }) => {
    await openApp(page, token);
    const writes = trackWrites(page);
    await page.locator('.tab-btn[data-tab="admin"]').click();
    await page.locator('#newRuleBtn').click();
    await page.locator('#ruleOperatorInput').selectOption('gt');
    await page.locator('#ruleValueInput').fill('');
    await page.locator('#ruleSaveBtn').click();
    await expect(page.locator('#ruleError')).toContainText('Enter a value');
    await page.locator('#ruleValueInput').fill('abc');
    await page.locator('#ruleSaveBtn').click();
    await expect(page.locator('#ruleError')).toContainText('Enter a number');
    expect(writes.filter(w => w.includes('/api/validation-rules'))).toEqual([]);
  });

  test('the theme form refuses a color that is not hex', async ({ page }) => {
    await openApp(page, token);
    const writes = trackWrites(page);
    await page.locator('.tab-btn[data-tab="admin"]').click();
    await page.locator('#openThemeModalBtn').click();
    await page.locator('#themeColorTxt_color_primary').fill('notacolor');
    await page.locator('#saveThemeBtn').click();
    await expect(page.locator('#notification')).toContainText('not valid');
    expect(writes.filter(w => w.includes('/api/theme'))).toEqual([]);
  });

  test('the What-If form keeps the multiplier from 0.1 to 5', async ({ page }) => {
    await openApp(page, token);
    const writes = trackWrites(page);
    await expect(page.locator('#whatIfMultiplier')).toHaveAttribute('max', '5');
    await page.evaluate(() => { _simProjectId = 1; });
    for (const bad of ['0', '6', '']) {
      // The card is hidden until a PEP is selected, so the test sets the value in the page.
      const message = await page.evaluate(async v => {
        document.getElementById('whatIfMultiplier').value = v;
        await _runWhatIf();
        return document.getElementById('whatIfError').textContent;
      }, bad);
      expect(message).toContain('from 0.1 to 5');
    }
    expect(writes.filter(w => w.includes('/simulate'))).toEqual([]);
  });
});
