import os from 'node:os';
import path from 'node:path';
import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end tests run against their own API and web servers on separate ports
 * (8001 / 3001) with a throw-away SQLite database, so they can never write to a
 * development or production database.
 */
const CI = !!process.env.CI;
const API_PORT = 8001;
const WEB_PORT = 3001;
const dbFile = path.join(os.tmpdir(), `shiftmaster-e2e-${Date.now()}.db`).replace(/\\/g, '/');

export const API_URL = `http://localhost:${API_PORT}/api/v1`;

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: CI ? 1 : 0,
  reporter: CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      // Locally, use the installed Google Chrome instead of downloading a browser
      use: { ...devices['Desktop Chrome'], ...(CI ? {} : { channel: 'chrome' }) },
    },
  ],
  webServer: [
    {
      command: `python -m uvicorn app.main:app --port ${API_PORT}`,
      cwd: '../../backend',
      url: `http://localhost:${API_PORT}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DATABASE_URL: `sqlite:///${dbFile}`,
        ENVIRONMENT: 'development',
        SECRET_KEY: 'e2e-secret-key',
        CORS_ORIGINS: `http://localhost:${WEB_PORT}`,
      },
    },
    {
      command: CI ? `npx next start -p ${WEB_PORT}` : `npx next dev -p ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}/login`,
      reuseExistingServer: false,
      timeout: 180_000,
      env: { NEXT_PUBLIC_API_URL: API_URL, NEXT_TELEMETRY_DISABLED: '1' },
    },
  ],
});
