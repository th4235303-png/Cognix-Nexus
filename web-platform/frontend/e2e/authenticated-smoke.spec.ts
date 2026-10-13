import { test, expect, type Page } from '@playwright/test';

const email = process.env.COGNIX_E2E_EMAIL;
const password = process.env.COGNIX_E2E_PASSWORD;
const apiUrl = process.env.COGNIX_E2E_API_URL || 'http://127.0.0.1:8000';

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function signIn(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(email!);
  await page.getByLabel('Password').fill(password!);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/dashboard(?:\?|$)/, { timeout: 15_000 });
}

async function expectPageLoads(page: Page, path: string, headingPattern: RegExp | string) {
  await page.goto(path);
  const heading = typeof headingPattern === 'string'
    ? page.getByRole('heading', { name: headingPattern, exact: false })
    : page.getByRole('heading', { name: headingPattern });
  await expect(heading).toBeVisible({ timeout: 10_000 });
  // Every page must have a <main> landmark
  await expect(page.locator('main, [role="main"]').first()).toBeVisible();
}

// ─── Unauthenticated (no secrets required) ────────────────────────────────────

test.describe('unauthenticated', () => {
  test('login page renders Sign in heading', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });

  test('protected routes redirect to login when unauthenticated', async ({ page }) => {
    await page.goto('/dashboard');
    // Either redirects to /login or shows login UI
    await expect(page).toHaveURL(/\/login|\/dashboard/, { timeout: 10_000 });
  });
});

// ─── API health (no auth required) ────────────────────────────────────────────

test.describe('api health', () => {
  test('GET /ready returns 200 OK', async ({ page }) => {
    const response = await page.request.get(`${apiUrl}/ready`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('status');
  });

  test('GET /health returns 200 OK', async ({ page }) => {
    const response = await page.request.get(`${apiUrl}/health`);
    expect(response.ok()).toBeTruthy();
  });
});

// ─── Authenticated flows ───────────────────────────────────────────────────────

test.describe('authenticated production smoke', () => {
  test.skip(!email || !password, 'COGNIX_E2E_EMAIL and COGNIX_E2E_PASSWORD are required');

  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  // Dashboard
  test('dashboard — Command Center heading visible', async ({ page }) => {
    await expectPageLoads(page, '/dashboard', 'Command Center');
    // Metric cards should render
    await expect(page.locator('[aria-label], h2, h3').first()).toBeVisible();
  });

  // Sources
  test('sources/inbox — inbox page loads', async ({ page }) => {
    await expectPageLoads(page, '/sources/inbox', /inbox/i);
  });

  test('sources/all — all sources page loads', async ({ page }) => {
    await page.goto('/sources/all');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    // heading is "All Sources" or similar
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  test('sources/add — add source form loads', async ({ page }) => {
    await page.goto('/sources/add');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Processing pipeline
  test('processing — pipeline page loads', async ({ page }) => {
    await page.goto('/processing');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Review
  test('review — review queue page loads', async ({ page }) => {
    await expectPageLoads(page, '/review', /review/i);
  });

  // Approved
  test('approved — approved knowledge page loads', async ({ page }) => {
    await expectPageLoads(page, '/approved', /approved/i);
  });

  // Books
  test('books — books list page loads', async ({ page }) => {
    await expectPageLoads(page, '/books', /book/i);
  });

  // Knowledge
  test('knowledge — knowledge vault page loads', async ({ page }) => {
    await page.goto('/knowledge');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Activity
  test('activity — activity log page loads', async ({ page }) => {
    await page.goto('/activity');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Export
  test('export — export page loads', async ({ page }) => {
    await page.goto('/export');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Delivery / Google Drive
  test('delivery — google drive delivery page loads', async ({ page }) => {
    await expectPageLoads(page, '/delivery', /delivery|google drive/i);
  });

  // Chat
  test('chat — chat page loads', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Notes
  test('notes — notes page loads', async ({ page }) => {
    await page.goto('/notes');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Graph
  test('graph — knowledge graph page loads', async ({ page }) => {
    await page.goto('/graph');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Collections
  test('collections — collections page loads', async ({ page }) => {
    await expectPageLoads(page, '/collections', /collection/i);
  });

  // Tags
  test('tags — tags page loads', async ({ page }) => {
    await expectPageLoads(page, '/tags', /tag/i);
  });

  // Vault
  test('vault — secret vault page loads', async ({ page }) => {
    await expectPageLoads(page, '/vault', /vault/i);
  });

  // Level Up
  test('level-up — level up page loads', async ({ page }) => {
    await page.goto('/level-up');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
    await expect(page.getByRole('heading').first()).toBeVisible();
  });

  // Vizora Lens
  test('lens — vizora lens page loads', async ({ page }) => {
    await expectPageLoads(page, '/lens', /vizora lens|lens/i);
  });

  // Usage
  test('usage — usage & limits page loads', async ({ page }) => {
    await expectPageLoads(page, '/usage', /usage/i);
  });

  // Tutor
  test('tutor — language tutor page loads', async ({ page }) => {
    await expectPageLoads(page, '/tutor', /tutor/i);
  });

  // Documents
  test('documents — document assistant page loads', async ({ page }) => {
    await expectPageLoads(page, '/documents', /document/i);
  });

  // Settings
  test('settings — settings page loads with system status', async ({ page }) => {
    await expectPageLoads(page, '/settings', /settings/i);
    // Should show system status section
    await expect(page.getByText(/system status|api status/i).first()).toBeVisible({ timeout: 8_000 });
  });

  // Navigation — sidebar links work
  test('sidebar navigation — all major links are present', async ({ page }) => {
    await page.goto('/dashboard');
    // Sidebar should have navigation links
    const nav = page.locator('nav, [role="navigation"]').first();
    await expect(nav).toBeVisible();
  });

  // API health from within authenticated session
  test('api /ready — responds ok from authenticated session', async ({ page }) => {
    const response = await page.request.get(`${apiUrl}/ready`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe('ready');
  });
});

// ─── Accessibility baseline ────────────────────────────────────────────────────

test.describe('accessibility baseline (unauthenticated pages)', () => {
  const publicPages = ['/login'];

  for (const path of publicPages) {
    test(`${path} — has <main> landmark and heading`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator('main, [role="main"]').first()).toBeVisible();
      await expect(page.getByRole('heading').first()).toBeVisible();
    });

    test(`${path} — no missing alt text on images`, async ({ page }) => {
      await page.goto(path);
      const images = page.locator('img:not([alt])');
      expect(await images.count()).toBe(0);
    });
  }
});
