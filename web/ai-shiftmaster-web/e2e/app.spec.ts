import { expect, Page, test } from '@playwright/test';
import { API_URL } from '../playwright.config';

// First visits compile pages in `next dev`, so navigation gets a generous timeout
const unique = () => Date.now().toString(36);

/** Navigate and wait until the page is hydrated (in `next dev` the first load also compiles it). */
async function open(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}

async function signIn(page: Page, email: string, password: string) {
  await open(page, '/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 60_000 });
}

async function apiToken(page: Page) {
  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  expect(token).toBeTruthy();
  return { Authorization: `Bearer ${token}` };
}

async function chooseOption(page: Page, label: string, option: string) {
  await page.getByLabel(label).click();
  // Only the open dropdown, matched by exact option title
  await page.locator(`.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option[title="${option}"]`).click();
}

test.describe('public pages', () => {
  test('landing page introduces the product', async ({ page }) => {
    await open(page, '/landing');
    await expect(page.getByRole('heading', { name: /Shift plans that/ })).toBeVisible();
    await page.getByRole('link', { name: /Start planning/ }).click();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole('heading', { name: 'Create your workspace' })).toBeVisible();
  });

  test('wrong password shows an error', async ({ page }) => {
    await open(page, '/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('not-the-password');
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test('protected pages redirect to sign-in', async ({ page }) => {
    await open(page, '/employees');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('error pages', () => {
  test('unknown addresses show the 404 page', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist');
    expect(response?.status()).toBe(404);
    await expect(page.getByRole('heading', { name: /doesn.t exist/ })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to home' })).toBeVisible();
  });

  test('employees opening an admin page see the 403 page', async ({ page }) => {
    await signIn(page, 'employee@example.com', 'employee123');
    await page.goto('/employees');
    await expect(page).toHaveURL(/\/forbidden/);
    await expect(page.getByRole('heading', { name: /access to this page/ })).toBeVisible();
  });
});

test('demo admin signs in and sees the dashboard', async ({ page }) => {
  await open(page, '/login');
  await page.getByRole('button', { name: 'Use the admin demo account' }).click();
  await expect(page.getByLabel('Email')).toHaveValue('admin@example.com');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 60_000 });
  await expect(page.getByText('Shifts by weekday')).toBeVisible();
  await expect(page.getByText(/Demo Company/)).toBeVisible();
});

test('a new company signs up, builds a team and schedules a week', async ({ page, request }) => {
  const id = unique();
  const company = `E2E Rail ${id}`;
  const adminEmail = `founder-${id}@e2e.example.com`;

  // Sign up creates a private workspace
  await open(page, '/register');
  await page.getByLabel('Company name').fill(company);
  await page.getByLabel('Full name').fill('Erin Founder');
  await page.getByLabel('Work email').fill(adminEmail);
  await page.getByLabel('Password', { exact: true }).fill('password123');
  await page.getByLabel('Confirm password').fill('password123');
  await page.getByText('I agree to the Terms of Service').click();
  await page.getByRole('button', { name: 'Create workspace' }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 60_000 });
  await expect(page.getByText(company)).toBeVisible();

  // The new workspace starts empty
  const headers = await apiToken(page);
  const employees = await request.get(`${API_URL}/employees`, { headers });
  expect((await employees.json()).total).toBe(0);

  // Departments and part of the team are created through the API to keep the test fast
  const dept = await request.post(`${API_URL}/departments`, { headers, data: { name: 'Operations', description: 'E2E' } });
  expect(dept.ok()).toBeTruthy();
  const departmentId = (await dept.json()).id;
  for (let i = 0; i < 5; i++) {
    const response = await request.post(`${API_URL}/employees`, {
      headers,
      data: {
        name: `Crew Member ${i}`,
        email: `crew${i}-${id}@e2e.example.com`,
        password: 'secret123',
        role: 'Operations Specialist',
        department_id: departmentId,
        preferences: { preferred_shift: ['morning', 'day', 'afternoon'][i % 3] },
      },
    });
    expect(response.ok()).toBeTruthy();
  }

  // Add one employee through the UI
  await open(page, '/employees');
  await page.getByRole('button', { name: 'Add employee' }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByLabel('Full name').fill('Uma Interface');
  await dialog.getByLabel('Email (used to sign in)').fill(`uma-${id}@e2e.example.com`);
  await dialog.getByPlaceholder('Enter or generate a password').fill('secret123');
  await chooseOption(page, 'Role', 'Operations Specialist');
  await chooseOption(page, 'Department', 'Operations');
  await dialog.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(page.getByText('Employee created')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Uma Interface' })).toBeVisible();

  // Generate and save a schedule
  await open(page, '/ai-optimization');
  await expect(page.getByText('Employees in scope')).toBeVisible();
  await page.getByRole('button', { name: /Generate schedule/ }).click();
  await expect(page.getByText('Optimization score')).toBeVisible();
  await expect(page.getByText(/Generated shifts \(\d+\)/)).toBeVisible();
  await page.getByRole('button', { name: 'Save schedule' }).click();
  await page.getByRole('button', { name: 'Confirm and save' }).click();
  await expect(page.getByText(/shifts saved to the schedule/)).toBeVisible();

  // Another company cannot see this team
  const demo = await request.post(`${API_URL}/auth/login`, { data: { email: 'admin@example.com', password: 'admin123' } });
  const demoHeaders = { Authorization: `Bearer ${(await demo.json()).access_token}` };
  const demoEmployees = await (await request.get(`${API_URL}/employees`, { headers: demoHeaders, params: { search: 'Uma Interface' } })).json();
  expect(demoEmployees.total).toBe(0);
});

test('signing out returns to the sign-in page', async ({ page }) => {
  await signIn(page, 'admin@example.com', 'admin123');
  await page.getByText('Admin User').click();
  await page.getByText(/Log ?out|Sign out/i).click();
  await expect(page).toHaveURL(/\/login|\/landing/);
});
