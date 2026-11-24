import os from 'node:os';
import path from 'node:path';
import fs from 'node:fs';
import { defineConfig, devices } from '@playwright/test';

// The flow tests (tests/frontend/e2e/flows) run against a second server with its own
// empty database. They change the administrator password, which the other specs must not see.
const FLOWS_PORT = 8001;
// Playwright loads this file again in every worker. Only the main process creates the database
// path, and the workers read it from the environment. Without this, a worker would delete the
// database that the server uses.
if (!process.env.PMAS_FLOWS_DB) {
  process.env.PMAS_FLOWS_DB = path.join(os.tmpdir(), `pmas-e2e-flows-${process.pid}.db`);
  for (const suffix of ['', '-wal', '-shm']) fs.rmSync(process.env.PMAS_FLOWS_DB + suffix, { force: true });
}
const flowsDb = process.env.PMAS_FLOWS_DB;

// Use the browser that Playwright installs. Set PW_CHROMIUM_PATH to use another binary.
const launchOptions = process.env.PW_CHROMIUM_PATH
  ? { executablePath: process.env.PW_CHROMIUM_PATH }
  : {};

export default defineConfig({
  testDir: './tests/frontend/e2e',
  timeout: 30000,
  retries: 0,
  workers: 1,   // both servers keep state, so the specs run one after the other
  use: {
    baseURL: 'http://127.0.0.1:8000',
    headless: true,
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      testIgnore: /flows\//,
      use: { ...devices['Desktop Chrome'], launchOptions },
    },
    {
      name: 'flows',
      testMatch: /flows\/.*\.spec\.js/,
      use: {
        ...devices['Desktop Chrome'],
        launchOptions,
        baseURL: `http://127.0.0.1:${FLOWS_PORT}`,
      },
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn backend.app.main:app --port 8000',
      port: 8000,
      reuseExistingServer: true,
      timeout: 30000,
      // Each test logs in. The default limit of 30 logins per minute is too low for the suite.
      env: { PMAS_LOGIN_RATE_LIMIT: '1000/minute' },
    },
    {
      command: `python -m uvicorn backend.app.main:app --port ${FLOWS_PORT}`,
      port: FLOWS_PORT,
      reuseExistingServer: false,
      timeout: 30000,
      env: {
        PMAS_DB_PATH: flowsDb,
        PMAS_PORT: String(FLOWS_PORT),
        PMAS_LOGIN_RATE_LIMIT: '1000/minute',
      },
    },
  ],
});
