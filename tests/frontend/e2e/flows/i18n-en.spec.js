import { test, expect } from '@playwright/test';
import { adminToken, auth, ensureCycle, uniquePep, timesheetCsv, uploadViaApi, openApp, createUser, loginViaForm } from './helpers.js';

// In English mode the interface must not show Portuguese words or raw translation keys.
const PORTUGUESE = /\b(Todos|Todas|Ativos?|Resolvidos?|Atualizar|Nível|Mensagem|Criado em|Central de Alertas|Alertas?\b|Por Ciclo|Selecionar|Sem opções|Notificações|ciclos|Carregando|Erro|Padrão|Orçamento|Estourado|Crítico|Atenção|Quarentena|Regra|Informações|Avisos|Importação|Usuário|Arquivo)\b/;
const RAW_KEY = /\b[a-z][a-z0-9]*(_[a-z0-9]+)*\.[a-z][A-Za-z0-9_.]*\b/;

test.describe('Flow: English interface', () => {
  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
    // A small budget and more hours than the budget make a budget alert.
    const pep = uniquePep();
    const res = await request.post('/api/projects', {
      headers: auth(token),
      data: { pep_wbs: pep, name: `Alert ${pep}`, budget_hours: 5, budget_cost: 1000, start_date: '2026-01-01', planned_end_date: '2026-06-30' },
    });
    expect(res.ok()).toBeTruthy();
    await uploadViaApi(request, token, `en-${pep}.csv`, timesheetCsv(pep, [['Eva English', '2026-01-05', 8], ['Eva English', '2026-01-06', 8]]));
  });

  /** Return the visible texts and the text attributes of the page. */
  const texts = page => page.evaluate(() => {
    const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    const out = [];
    document.querySelectorAll('body *').forEach(el => {
      if (!visible(el) || el.closest('script, style, svg, #loginOverlay')) return;
      const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).filter(Boolean);
      own.forEach(t => out.push(t));
      ['title', 'aria-label', 'placeholder'].forEach(a => { if (el.getAttribute(a)) out.push(el.getAttribute(a)); });
      if (el.tagName === 'SELECT') [...el.options].forEach(o => out.push(o.textContent.trim()));
    });
    return out;
  });

  async function check(page, label) {
    await page.waitForTimeout(600);
    const all = await texts(page);
    // The alert message comes from the server. The language of server messages is a separate decision.
    const portuguese = all.filter(t => PORTUGUESE.test(t) && !/^Projeto '/.test(t));
    expect(portuguese, `${label}: Portuguese text`).toEqual([]);
    // A raw key looks like "area.name". Skip file names, numbers and PEP codes.
    const keys = all.filter(t => RAW_KEY.test(t) && !/\s|\.(csv|xlsx)$|^\d/.test(t) && !/^[A-Z0-9-]+$/.test(t));
    expect(keys, `${label}: raw translation keys`).toEqual([]);
  }

  test('every tab shows English text only', async ({ page }) => {
    await openApp(page, token);
    await page.locator('#loadBtn').click();
    await check(page, 'Dashboard / Effort');
    await page.locator('.atab-btn[data-atab="portfolio"]').click();
    await check(page, 'Dashboard / Portfolio');
    await page.locator('.atab-btn[data-atab="forecast"]').click();
    await check(page, 'Dashboard / Forecast');
    for (const tab of ['projects', 'cycles', 'team']) {
      await page.locator(`.tab-btn[data-tab="${tab}"]`).click();
      await check(page, tab);
    }
    await page.locator('.tab-btn[data-tab="my"]').click();
    for (const sub of ['profile', 'upload']) {   // the alerts sub-tab is for users who are not administrators
      await page.locator(`[data-my-tab="${sub}"]`).click();
      await check(page, `my area / ${sub}`);
    }
    await page.locator('.tab-btn[data-tab="admin"]').click();
    await check(page, 'admin');
  });

  test('the alert tables use English labels', async ({ page }) => {
    await openApp(page, token);
    await page.locator('.tab-btn[data-tab="admin"]').click();
    await expect(page.locator('#adminAlertsBody tr').first()).toBeVisible();
    await expect(page.locator('#adminAlertsTable thead')).toContainText('Level');
    await expect(page.locator('#adminAlertsBody')).toContainText(/Budget|Schedule/);
    await expect(page.locator('#adminAlertsBody')).toContainText(/Critical|Warning/);
  });

  test('the alerts of a user show English text', async ({ page, request }) => {
    const user = await createUser(request, token);
    await loginViaForm(page, user.username, user.password);
    await page.locator('.tab-btn[data-tab="my"]').click();
    await page.locator('[data-my-tab="alerts"]').click();
    await expect(page.locator('#myAlertsBody tr').first()).toBeVisible();
    await check(page, 'my area / alerts');
    await expect(page.locator('#myAlertsTable thead')).toContainText('Level');
    await expect(page.locator('#myAlertsBody')).toContainText(/Budget|Schedule/);
  });
});
