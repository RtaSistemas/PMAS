import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import { adminToken, auth, uniquePep, openApp } from './helpers.js';

test.describe('Flow: CSV export is safe and the import restores the text', () => {
  test('a project name that looks like a formula is exported with a quote and imported back unchanged', async ({ page, request }) => {
    const token = await adminToken(request);
    const pep = uniquePep();
    const name = '=HYPERLINK("http://x")';
    const created = await request.post('/api/projects', {
      headers: auth(token),
      data: { pep_wbs: pep, name, client: '-Cliente "A"', manager: '@gerente', budget_hours: 10, budget_cost: 1000 },
    });
    expect(created.ok()).toBeTruthy();

    const errors = await openApp(page, token);
    await page.locator('.tab-btn[data-tab="projects"]').click();
    await page.waitForFunction(p => _allProjects.some(x => x.pep_wbs === p), pep);

    const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#exportProjectsBtn').click()]);
    const text = fs.readFileSync(await download.path(), 'utf8').replace(/^﻿/, '');
    const line = text.split('\n').find(l => l.includes(pep));
    expect(line, 'the project is in the export').toBeTruthy();
    // Text cells are quoted and start with a single quote before the trigger.
    expect(line).toContain(`"'=HYPERLINK(""http://x"")"`);
    expect(line).toContain(`"'-Cliente ""A"""`);
    expect(line).toContain(`"'@gerente"`);
    expect(line).not.toMatch(/(^|,)"=/);          // no cell starts with a bare trigger

    // The project goes away, then the exported file brings it back with the original text.
    const list = await (await request.get('/api/projects', { headers: auth(token) })).json();
    const id = list.find(p => p.pep_wbs === pep).id;
    expect((await request.delete(`/api/projects/${id}`, { headers: auth(token) })).ok()).toBeTruthy();
    const imported = await request.post('/api/projects/import', {
      headers: auth(token),
      multipart: { file: { name: 'projetos.csv', mimeType: 'text/csv', buffer: Buffer.from(`${text.split('\n')[0]}\n${line}\n`) } },
    });
    expect(imported.ok()).toBeTruthy();
    const back = (await (await request.get('/api/projects', { headers: auth(token) })).json()).find(p => p.pep_wbs === pep);
    expect(back.name).toBe(name);
    expect(back.client).toBe('-Cliente "A"');
    expect(back.manager).toBe('@gerente');
    expect(errors).toEqual([]);
  });
});
