# Cognix Nexus — Deployment

## Production services
- Render API: Cognix-Core, main branch, auto deploy enabled.
- Render worker: cognix-core-worker-runtime, main branch; deploy policy currently manual.
- Netlify frontend: deployment intentionally paused until release candidate verification.
- Supabase: production database/Auth/storage.

## Release sequence
1. CI green on main.
2. Apply/verify database migrations.
3. Deploy API and worker from the intended main revision.
4. Verify /health and /ready.
5. Verify worker queue and logs.
6. Run provider/storage smoke tests.
7. Run frontend production smoke.
8. Only then re-enable frontend promotion/release.

## Required production configuration
- Database URL and database-required mode.
- Auth/JWKS issuer/audience.
- Explicit CORS/allowed hosts.
- AI provider configuration.
- Google OAuth/Drive configuration.
- Storage provider secrets.
- Optional Sentry DSN.

## Rollback
Stop promotion first. Keep the last known-good deploy available, verify database compatibility, then roll back application services. Database destructive rollback is never assumed safe; use forward-compatible migrations or an isolated restore drill.