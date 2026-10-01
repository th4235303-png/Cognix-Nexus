# Cognix Core Operations

## Deployment model

- Frontend: Netlify (`web-platform/frontend`)
- API: Render web service (`web-platform/backend`)
- Worker: Render worker (`web-platform/backend`)
- Persistence: PostgreSQL / Supabase

During active development, Netlify continuous builds are intentionally paused by `netlify.toml`. Re-enable them by setting `COGNIX_NETLIFY_DEPLOY=true` in the Netlify build environment.

## Required production checks

1. Set `COGNIX_ENV=production`.
2. Configure `DATABASE_URL` and confirm `/ready` reports `database_reachable=true`.
3. Set `COGNIX_REQUIRE_DATABASE=true` so readiness cannot silently accept memory-only persistence.
4. Set `COGNIX_AUTH_REQUIRED=true` and configure JWT verification.
5. Set explicit `COGNIX_CORS_ORIGINS` and `COGNIX_ALLOWED_HOSTS`.
6. Configure AI/Drive providers only through secret environment variables.
7. Configure `SENTRY_DSN` if error monitoring is desired.
8. Keep Netlify deploys paused until the release candidate has passed CI and manual smoke testing.

## Health semantics

- `/health` is a liveness endpoint and does not require the database.
- `/ready` checks database reachability when persistence is configured or required.
- A `not_ready` response should prevent traffic from being considered healthy by the deployment platform.

## Release verification

Run the same checks used by CI:

- Frontend: `npm ci`, `npm run typecheck`, `npm run lint`, `npm run build`
- Backend: `python -m compileall app`, `python -m unittest discover -s tests`

Then smoke-test authentication, upload limits, Brain Vault retrieval, worker processing, exports, and the health/readiness endpoints against the target environment.

## Rollback

If a release introduces a regression, stop promotion first. Restore the previous known-good application revision and keep the database schema compatible with both revisions before rolling back migrations. Do not delete or rewrite evidence/source records as part of an application rollback.
