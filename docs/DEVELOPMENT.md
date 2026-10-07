# Cognix Nexus — Development

> Owner: Development workflow
> Update when: local setup, build/test commands, or development prerequisites change
> Last Updated: 2026-10-08
> Do NOT put here: production evidence or release status.

## Repository layout

- `web-platform/frontend` — Next.js frontend.
- `web-platform/backend` — FastAPI API and worker.
- `mobile` — Expo mobile client.
- `supabase/migrations` — database migration ledger.

## Frontend

Use the frontend package manager/lockfile committed in `web-platform/frontend`. Core stack: Next.js 15.x, React 18.x, TypeScript and Tailwind CSS.

Expected checks:
- install dependencies from the lockfile;
- typecheck;
- lint;
- production build.

## Backend

The backend uses FastAPI/Python with a dedicated worker. Key runtime dependencies include PostgreSQL/psycopg, JWT verification, Google API clients, PDF/EPUB/image processing, boto3 and Sentry.

Expected checks:
`python -m compileall app`
and
`python -m unittest discover -s tests`

## Mobile

The mobile foundation uses Expo. Production device/EAS verification remains an external gate.

## Database development

Schema changes are registered in `supabase/migrations` and must be verified in CI and against the intended production state before release.

The repository currently reaches migration 032. The duplicate `010` numbering defect is documented in `docs/DATABASE.md`; do not silently rename historical migrations.

## Working rule

All implementation/documentation changes land on main. Follow `TOOL.md` and preserve the canonical documentation ownership model.
