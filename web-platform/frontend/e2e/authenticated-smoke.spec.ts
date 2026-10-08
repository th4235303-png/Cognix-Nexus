import { test, expect } from '@playwright/test';

const email = process.env.COGNIX_E2E_EMAIL;
const password = process.env.COGNIX_E2E_PASSWORD;

test.describe('authenticated production smoke', () => {
  test.skip(!email || !password, 'COGNIX_E2E_EMAIL and COGNIX_E2E_PASSWORD are required');

  test('signs in and reaches the private dashboard', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await page.getByLabel('Email').fill(email!);
    await page.getByLabel('Password').fill(password!);
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/dashboard(?:\?|$)/);
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();

    const apiResponse = await page.request.get(
      (process.env.COGNIX_E2E_API_URL || 'http://127.0.0.1:8000') + '/ready',
    );
    expect(apiResponse.ok()).toBeTruthy();
  });
});
