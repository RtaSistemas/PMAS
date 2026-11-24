import { test, expect } from '@playwright/test';
import { adminToken, ensureCycle, createProject, uniquePep, timesheetCsv, uploadViaApi, openApp } from './helpers.js';

// Text from a CSV file must show as text in the chart tooltips. It must never become HTML.
test.describe('Flow: HTML in CSV text', () => {
  const who = 'Bruno <b>Costa</b>';
  let token;
  test.beforeAll(async ({ request }) => {
    token = await adminToken(request);
    await ensureCycle(request, token);
    const pep = uniquePep();
    await createProject(request, token, pep);
    await uploadViaApi(request, token, `escape-${pep}.csv`, timesheetCsv(pep, [[who, '2026-01-08', 6]]));
  });

  test('a collaborator name with HTML shows as text in the Effort tooltip', async ({ page }) => {
    const errors = await openApp(page, token);
    await page.locator('#loadBtn').click();
    await page.waitForFunction(() => {
      const chart = echarts.getInstanceByDom(document.getElementById('effortChart'));
      return chart && chart.getOption().yAxis?.[0]?.data?.some(n => String(n).includes('Bruno'))
        || chart && chart.getOption().xAxis?.[0]?.data?.some(n => String(n).includes('Bruno'));
    });
    const html = await page.evaluate(() => {
      const chart = echarts.getInstanceByDom(document.getElementById('effortChart'));
      const opt = chart.getOption();
      const axis = (opt.yAxis?.[0]?.type === 'category' ? opt.yAxis : opt.xAxis)[0];
      const dataIndex = axis.data.findIndex(n => String(n).includes('Bruno'));
      chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex });
      // The tooltip is a div without a chart (svg) inside it.
      const tip = [...document.querySelectorAll('#effortChart div')]
        .find(d => !d.querySelector('svg, canvas') && d.textContent.includes('Total'));
      return { inner: tip?.innerHTML ?? '', text: tip?.textContent ?? '', bold: tip ? [...tip.querySelectorAll('b')].map(b => b.textContent) : [] };
    });
    expect(html.text, 'the tooltip is open').toContain('Total');
    expect(html.text).toContain('Bruno <b>Costa</b>');
    expect(html.bold).not.toContain('Costa');
    expect(errors).toEqual([]);
  });
});
