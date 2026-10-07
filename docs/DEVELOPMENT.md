# Cognix Nexus — Development

> Owner: Development workflow
> Update when: local setup, build/test commands, or development prerequisites change
> Last Updated: 2026-10-08
> Do NOT put here: production evidence or release status.

## Repository layout
- web-platform/frontend — Next.js frontend.
- web-platform/backend — FastAPI API and worker.
- mobile — Expo mobile client.
- supabase/migrations — database migration ledger.

## Frontend
Core stack: Next.js 15.x, React 18.x, TypeScript and Tailwind CSS. Use the committed lockfile and run typecheck, lint and production build checks.

## Backend
FastAPI/Python with a dedicated worker. Runtime includes PostgreSQL/psycopg, JWT verification, Google API clients, PDF/EPUB/image processing, boto3 and Sentry. Expected checks: python -m compileall app and python -m unittest discover -s tests.

## Mobile
Expo foundation exists. Production device/EAS verification remains an external gate.

## Database development
Schema changes are registered in supabase/migrations and verified in CI and against intended production state. Repository head is 032. The duplicate 010 numbering defect is documented in docs/DATABASE.md; do not silently rename historical migrations.

## Working rule
All implementation/documentation changes land on main. Follow TOOL.md and preserve canonical documentation ownership.
