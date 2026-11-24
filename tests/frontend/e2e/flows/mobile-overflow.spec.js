import { test, expect, devices } from '@playwright/test';
import { adminToken, auth, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp, createUser } from './helpers.js';

const pixel = devices['Pixel 5'];

// The page must not scroll sideways on a phone. A wide table must scroll inside its own box.
test.describe('Flow: no horizontal page scroll on a phone', () => {
  test.use({ viewport: pixel.viewport, userAgent: pixel.userAgent });

  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    await uploadViaApi(request, token, `m-${pep}.csv`, timesheetCsv(pep, [
      ['Mara Mobile', '2026-01-05', 8], ['Nico Mobile', '2026-01-06', 8], ['Mara Mobile', '2026-01-12', 4],
    ]));
    // A user rule shows all the action buttons, and a second user fills the user table.
    await request.post('/api/validation-rules', {
      headers: auth(token),
      data: {
        field: 'horas_individuais', operator: 'gt', value: '12', action: 'warning', order: 50, is_active: true,
        description: 'A long description of the rule, so that the line must wrap on a narrow screen',
      },
    });
    await createUser(request, token);
  });

  const overflow = page => page.evaluate(() => ({
    scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
    view: window.innerWidth,
    wide: [...document.querySelectorAll('body *')]
      .filter(el => el.offsetParent !== null && el.getBoundingClientRect().right > window.innerWidth + 20
        && !el.closest('.table-responsive, .overflow-x, .app-tabs, .modal-backdrop, #notifPanel'))
      .slice(0, 5)
      .map(el => {
        const path = [];
        for (let n = el; n && n !== document.body && path.length < 6; n = n.parentElement) {
          path.push(`${n.tagName}${n.id ? '#' + n.id : ''}${typeof n.className === 'string' && n.className ? '.' + n.className.split(' ')[0] : ''}`);
        }
        return `${path.join(' < ')} right=${Math.round(el.getBoundingClientRect().right)}`;
      }),
  }));

  async function expectFits(page, label) {
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(700);   // the tables fill after the requests end
    const o = await overflow(page);
    expect(o.scroll, `${label}: page width ${o.scroll}px, viewport ${o.view}px, wide: ${o.wide.join(' | ')}`).toBeLessThanOrEqual(o.view + 20);
    expect(o.wide, `${label}: elements outside the screen`).toEqual([]);
  }

  test('every tab fits the screen', async ({ page }) => {
    await openApp(page, token);
    await page.locator('#loadBtn').click();
    await expectFits(page, 'Dashboard / Effort');

    await page.locator('.atab-btn[data-atab="portfolio"]').click();
    await expect(page.locator('#runwayTable tbody tr').first()).toBeVisible();
    await expectFits(page, 'Dashboard / Portfolio');

    await page.locator('.atab-btn[data-atab="forecast"]').click();
    await expectFits(page, 'Dashboard / Forecast');

    for (const tab of ['projects', 'cycles', 'team', 'my', 'admin']) {
      await page.locator(`.tab-btn[data-tab="${tab}"]`).click();
      await expectFits(page, tab);
    }
  });
});
