// Shared helpers for the flow tests. They use the API for set-up and the UI for the flow under test.
import { expect } from '@playwright/test';

export const ADMIN_PASSWORD = 'E2e#Passw0rd';

const login = (request, password) =>
  request.post('/api/token', { form: { username: 'admin', password } });

/** Return an administrator token. The first call replaces the default password. */
export async function adminToken(request) {
  let res = await login(request, ADMIN_PASSWORD);
  if (!res.ok()) {
    const first = await login(request, 'admin');
    if (first.ok()) {
      const temp = (await first.json()).access_token;
      const change = await request.patch('/api/users/1/password', {
        headers: { Authorization: `Bearer ${temp}` },
        data: { new_password: ADMIN_PASSWORD },
      });
      expect(change.ok(), 'password change').toBeTruthy();
    }
    res = await login(request, ADMIN_PASSWORD);   // also covers a change that another worker made
  }
  expect(res.ok(), 'admin login').toBeTruthy();
  return (await res.json()).access_token;
}

export const auth = token => ({ Authorization: `Bearer ${token}` });

/** A short unique PEP code that matches the ingestion pattern (letters or digits, a dash, 3 or more). */
export function uniquePep() {
  return `E2E-${Math.random().toString(36).slice(2, 7).toUpperCase().padEnd(5, 'X')}`;
}

export async function ensureCycle(request, token, name = 'E2E Jan 2026') {
  const list = await (await request.get('/api/cycles', { headers: auth(token) })).json();
  if (list.some(c => c.name === name)) return;
  const res = await request.post('/api/cycles', {
    headers: auth(token),
    data: { name, start_date: '2026-01-01', end_date: '2026-01-31' },
  });
  expect(res.ok(), 'create cycle').toBeTruthy();
}

export async function createProject(request, token, pep) {
  const res = await request.post('/api/projects', {
    headers: auth(token),
    data: {
      pep_wbs: pep, name: `Project ${pep}`, budget_hours: 1000, budget_cost: 100000,
      start_date: '2026-01-01', planned_end_date: '2026-06-30',
    },
  });
  expect(res.ok(), 'create project').toBeTruthy();
  return res.json();
}

const HEADER = 'Colaborador,Data,Horas totais (decimal),Código PEP,PEP';

/** Build a timesheet CSV. Each row is [collaborator, date, hours]. */
export function timesheetCsv(pep, rows) {
  const lines = rows.map(([who, date, hours]) => `${who},${date},${hours},${pep},Project ${pep}`);
  return [HEADER, ...lines].join('\n') + '\n';
}

export async function uploadViaApi(request, token, name, csv) {
  const res = await request.post('/api/upload-timesheet', {
    headers: auth(token),
    multipart: { file: { name, mimeType: 'text/csv', buffer: Buffer.from(csv, 'utf-8') } },
  });
  expect(res.ok(), 'upload').toBeTruthy();
  return res.json();
}

/** Open the app as the administrator, in English, without the login form. Return the list of page errors. */
export async function openApp(page, token) {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(t => {
    sessionStorage.setItem('access_token', t);
    localStorage.setItem('pmas_lang', 'en');
  }, token);
  await page.goto('/frontend/index.html');
  await expect(page.locator('#appShell')).toBeVisible();
  return errors;
}

/**
 * Create a non-admin user through the API and return its credentials.
 * If the server marks the password as temporary, this helper replaces it, so the user can log in.
 */
export async function createUser(request, token, role = 'user') {
  const username = `u${Math.random().toString(36).slice(2, 9)}`;
  const password = 'User#Passw0rd1';
  const res = await request.post('/api/users', { headers: auth(token), data: { username, password, role } });
  expect(res.ok(), 'create user').toBeTruthy();
  const created = await res.json();
  const login = await request.post('/api/token', { form: { username, password } });
  expect(login.ok(), 'user login').toBeTruthy();
  const body = await login.json();
  const payload = JSON.parse(Buffer.from(body.access_token.split('.')[1], 'base64url').toString());
  if (payload.must_change) {
    const next = `${password}x`;
    const change = await request.patch(`/api/users/${created.id}/password`, {
      headers: auth(body.access_token), data: { new_password: next, current_password: password },
    });
    expect(change.ok(), 'first password change').toBeTruthy();
    return { id: created.id, username, password: next };
  }
  return { id: created.id, username, password };
}

/** Sign in through the real login form, in English. Return the lists of page errors and of 403 responses. */
export async function loginViaForm(page, username, password) {
  const seen = { errors: [], forbidden: [] };
  page.on('pageerror', e => seen.errors.push(e.message));
  page.on('response', r => { if (r.status() === 403) seen.forbidden.push(r.url()); });
  await page.addInitScript(() => localStorage.setItem('pmas_lang', 'en'));
  await page.goto('/frontend/index.html');
  await page.locator('#loginUsername').fill(username);
  await page.locator('#loginPassword').fill(password);
  await page.locator('#loginForm button[type="submit"]').click();
  await expect(page.locator('#appShell')).toBeVisible();
  return seen;
}
