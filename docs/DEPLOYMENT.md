# Cognix Nexus — Deployment

> Owner: Deployment/release operations
> Update when: hosting, deployment configuration, environment requirements, or rollback procedure changes
> Last Updated: 2026-10-08
> Do NOT put here: product roadmap or live evidence tables.

## Production targets

- Frontend: Netlify.
- API: Render.
- Worker: Render.
- Database/Auth: Supabase/PostgreSQL.
- Storage: Cloudinary + Supabase Storage + B2, with Google Drive for user-owned export/backup.

The checked-in Render blueprint declares API and worker services with commit-triggered deployment behavior. Prior live evidence says the worker remained manual/off. **Live worker deployment policy is VERIFY.**

Netlify production promotion remains gated by the release candidate.

## Release sequence

1. CI green on main.
2. Apply/verify database migrations.
3. Deploy API and worker from intended main revision.
4. Verify `/health` and `/ready`.
5. Verify worker queue/logs.
6. Run provider/storage smoke tests.
7. Run frontend production smoke.
8. Reconcile release evidence.
9. Only then promote/tag the release.

## Required production configuration

- `DATABASE_URL` and database-required mode.
- Auth/JWKS issuer/audience.
- Explicit CORS/allowed hosts.
- AI provider settings.
- Google OAuth/Drive settings.
- Storage provider secrets.
- Optional Sentry DSN.

Secrets are backend-only and never committed.

## Google Drive

OAuth/export implementation exists. Real account consent, refresh-token issuance and export verification remain pending/deferred until the account owner performs the activation drill.

## Netlify

The frontend build is rooted at `web-platform/frontend`. Production deployment must use the intended main revision and pass the UI smoke/release gates.

## Rollback

Stop promotion first. Keep the last known-good application revision available. Verify database compatibility before application rollback. Never assume a destructive database rollback is safe; prefer forward-compatible migrations or an isolated restore drill.

## External activation

Storage, Drive, AI and monitoring activation procedures are retained in `docs/STORAGE.md` and `docs/runbooks/external-activation.md`.
