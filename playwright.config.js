import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/frontend/e2e',
  timeout: 30000,
  retries: 0,
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
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'python -m uvicorn backend.app.main:app --port 8000',
    port: 8000,
    reuseExistingServer: true,
    timeout: 30000,
  },
});
