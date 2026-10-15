/**
 * Cognix Nexus — Accessibility E2E Tests
 *
 * Uses @axe-core/playwright to run automated WCAG AA checks on every
 * authenticated page. Also verifies basic keyboard navigability.
 *
 * Env vars
 *  COGNIX_E2E_EMAIL    – test-user email    (required for auth)
 *  COGNIX_E2E_PASSWORD – test-user password (required for auth)
 *  COGNIX_E2E_BASE_URL – frontend base URL  (consumed by playwright.config.ts)
 *
 * Install dependency (if not already present):
 *   npm i -D @axe-core/playwright
 */

import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// ---------------------------------------------------------------------------
// Env
// ---------------------------------------------------------------------------
const email    = process.env.COGNIX_E2E_EMAIL;
const password = process.env.COGNIX_E2E_PASSWORD;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
async function signIn(page: Page): Promise<void> {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  await page.getByLabel('Email').fill(email!);
  await page.getByLabel('Password').fill(password!);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/dashboard(?:\?|$)/);
}

/**
 * Run axe on the current page and assert no WCAG AA violations.
 * Tags chosen: wcag2a, wcag2aa, wcag21aa — covers the most common WCAG 2.1 AA rules.
 */
async function assertNoAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    // Exclude third-party embeds that we cannot control
    .exclude('[data-axe-ignore]')
    .analyze();

  // Filter out "incomplete" results (axe couldn't determine pass/fail) to
  // keep the report focused on confirmed violations.
  expect(
    results.violations,
    `Axe violations on ${page.url()}:\n` +
      results.violations
        .map(
          (v) =>
            `  [${v.impact ?? 'unknown'}] ${v.id}: ${v.description}\n` +
            v.nodes.map((n) => `    -> ${n.html}`).join('\n'),
        )
        .join('\n'),
  ).toHaveLength(0);
}

/**
 * Verify that pressing Tab from the start of the page produces at least one
 * focusable element (keyboard navigability baseline).
 */
async function assertKeyboardNavigable(page: Page): Promise<void> {
  await page.keyboard.press('Tab');
  // A focusable element should now be active
  const focused = page.locator(':focus');
  await expect(focused).toBeVisible({ timeout: 5_000 });
}

// ---------------------------------------------------------------------------
// Authenticated pages under test
// ---------------------------------------------------------------------------
const PAGES: { path: string; heading: string }[] = [
  { path: '/dashboard',    heading: 'Command Center'      },
  { path: '/sources/add',  heading: 'Add Source'          },
  { path: '/sources/inbox',heading: 'Source Inbox'        },
  { path: '/sources/all',  heading: 'All Sources'         },
  { path: '/review',       heading: 'Review Center'       },
  { path: '/approved',     heading: 'Approved Knowledge'  },
  { path: '/processing',   heading: 'Processing Queue'    },
  { path: '/books',        heading: 'Book Library'        },
  { path: '/knowledge',    heading: 'Knowledge Vault'     },
  { path: '/activity',     heading: 'Activity Log'        },
  { path: '/settings',     heading: 'Settings'            },
  { path: '/export',       heading: 'Unified Export'      },
  { path: '/delivery',     heading: 'Google Drive Delivery' },
  { path: '/chat',         heading: 'Brain Query'         },
  { path: '/notes',        heading: 'Second Brain'        },
  { path: '/graph',        heading: 'Knowledge Graph'     },
  { path: '/collections',  heading: 'Collections'         },
  { path: '/tags',         heading: 'Tags & Topics'       },
  { path: '/vault',        heading: 'Secret Vault'        },
  { path: '/level-up',     heading: 'Level Up 20'         },
  { path: '/lens',         heading: 'Vizora Lens'         },
  { path: '/usage',        heading: 'Usage & Limits'      },
  { path: '/tutor',        heading: 'Language Tutor'      },
  { path: '/documents',    heading: 'Document Assistant'  },
];

// ---------------------------------------------------------------------------
// Suite — Authenticated accessibility checks
// ---------------------------------------------------------------------------
test.describe('accessibility — authenticated pages', () => {
  test.skip(!email || !password, 'COGNIX_E2E_EMAIL and COGNIX_E2E_PASSWORD are required');

  /**
   * Sign in once before each test instead of sharing state across parallel
   * workers to keep tests independent and deterministic.
   */
  test.beforeEach(async ({ page }) => {
    await signIn(page);
  });

  for (const { path, heading } of PAGES) {
    // -----------------------------------------------------------------------
    // WCAG AA axe scan
    // -----------------------------------------------------------------------
    test(`axe WCAG AA — ${path}`, async ({ page }) => {
      await page.goto(path);
      // Wait for the page heading to be visible so content is rendered
      await expect(
        page.getByRole('heading', { name: heading, level: 1 }),
      ).toBeVisible();
      await assertNoAxeViolations(page);
    });

    // -----------------------------------------------------------------------
    // <main> landmark
    // -----------------------------------------------------------------------
    test(`has <main> landmark — ${path}`, async ({ page }) => {
      await page.goto(path);
      await expect(
        page.getByRole('heading', { name: heading, level: 1 }),
      ).toBeVisible();
      await expect(page.locator('main')).toBeVisible();
    });

    // -----------------------------------------------------------------------
    // Keyboard navigability
    // -----------------------------------------------------------------------
    test(`keyboard navigable — ${path}`, async ({ page }) => {
      await page.goto(path);
      await expect(
        page.getByRole('heading', { name: heading, level: 1 }),
      ).toBeVisible();
      await assertKeyboardNavigable(page);
    });
  }
});

// ---------------------------------------------------------------------------
// Suite — Public / unauthenticated pages
// ---------------------------------------------------------------------------
test.describe('accessibility — public pages', () => {
  test('axe WCAG AA — /login', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await assertNoAxeViolations(page);
  });

  test('has <main> landmark — /login', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('main')).toBeVisible();
  });

  test('keyboard navigable — /login', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await assertKeyboardNavigable(page);
  });
});
