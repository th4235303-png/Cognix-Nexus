# Cognix Nexus — Deployment

> Owner: Deployment/release operations
> Update when: hosting, deployment configuration, environment requirements, or rollback procedure changes
> Last Updated: 2026-10-15
> Do NOT put here: product roadmap or live evidence tables.

## Current production targets

- Frontend: **Render** (`cognix-nexus-frontend`).
- API: **Render** (`Cognix-Core`).
- Worker: **Render** (`cognix-core-worker-runtime`).
- Database/Auth: **Supabase/PostgreSQL**.
- Storage: Cloudinary + Supabase Storage + Backblaze B2, with Google Drive for user-owned export/backup.
- Cloudflare: connected account but no active zone/Workers/Pages resource currently verified; R2 is not enabled.
- Vercel: no repository configuration or connected deployment evidence verified.
- Netlify: legacy frontend target; no active Netlify service is verified by the current connected infrastructure audit.

## Render — current live configuration

### Frontend

- Service: `cognix-nexus-frontend`
- Runtime: Node
- Repository: `th4235303-png/Cognix-Nexus`
- Branch: `main`
- Build: `cd web-platform/frontend && npm ci && npm run build`
- Start: `cd web-platform/frontend && npm start`
- Region: Singapore

### API

- Service: `Cognix-Core`
- Runtime: Python
- Root: `web-platform/backend`
- Build: `pip install -r requirements.lock`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Auto-deploy: commit

### Worker

- Service: `cognix-core-worker-runtime`
- Runtime: Python
- Root: `web-platform/backend`
- Build: `pip install -r requirements.lock`
- Start: `python -m app.worker`
- Health check: `/health`
- Auto-deploy: commit

## 2026-10-15 deployment finding

The latest worker deploy for commit `5067c12b3235a87b2881f320350706b54ee0b5a2` is **live**. The corresponding API deploy `dep-db7q3t142hec739i2s6g` **failed after a successful build** with a non-zero exit. The API's previous live revision remains the last known-good runtime. Diagnose the startup/runtime failure before treating the revision as releasable.

The connected Render action surface can inspect services/deploys/logs and trigger deploys, but it cannot enumerate or delete individual live environment variables. Do not claim live-vs-blueprint parity until a safe environment-name inventory is captured.

## Release sequence

1. CI green on the intended main revision.
2. Apply/verify database migrations.
3. Deploy frontend, API and worker from the intended revision.
4. Diagnose any failed deployment before continuing.
5. Verify API `/health` and `/ready` externally.
6. Verify worker startup, persistence and queue/log behavior.
7. Reconcile environment-variable names against code, `render.yaml`, workflows and recovery/test procedures.
8. Run provider/storage/Book acceptance.
9. Run authenticated frontend/browser smoke.
10. Run accessibility/performance/mobile/Sentry/GDPR/recovery gates.
11. Complete grouped manual verification last.
12. Run final production smoke.
13. Approve and tag the release.

## Required production configuration

Keep required database/auth/JWKS/CORS/host configuration, provider credentials, Google OAuth/Drive values, storage credentials/settings, E2E/recovery/release-gate variables, and optional Sentry DSN as appropriate for each service. AI endpoints and model IDs are code-defined; do not configure provider model or URL overrides. `COHERE_API_KEY` is currently required for the AI release-gate preflight because production vectors use dimension 1536. Secrets are backend-only and never committed.

## Frontend hosting reconciliation

The repository previously documented Netlify as the frontend host, but the connected Render account currently has an active `cognix-nexus-frontend` service built directly from the repository. Until a different platform is intentionally selected and verified, Render is the authoritative operational target. If Vercel is desired, establish the project, domain, environment variables and deployment pipeline explicitly rather than documenting an assumed migration.

## Google Drive

OAuth/export implementation exists. Real account authorization, folder access, export, retry and idempotency verification remain release gates.

## Cloudflare

Cloudflare is currently optional/legacy infrastructure. The 2026-10-15 account audit found no zones, Workers scripts or Pages projects, and the R2 API reports that R2 must first be enabled through the dashboard. Do not treat Cloudflare as an active production dependency until a resource is intentionally provisioned and tested.

## Rollback

Stop promotion first. Keep the last known-good application revision available. Verify database compatibility before application rollback. Never assume a destructive database rollback is safe; prefer forward-compatible migrations or an isolated restore drill.

## Environment-variable cleanup

Do not delete variables based only on a guessed naming pattern. Compare the actual live names against code, workflows, `render.yaml` and test/recovery procedures. Remove only verified-unused model/URL/legacy routing overrides. Never replace the whole environment unless every retained variable has been inventoried and verified. Record the cleanup and restart/deploy evidence.

## External activation

Storage, Drive, AI and monitoring activation procedures are in `docs/STORAGE.md` and `docs/runbooks/external-activation.md`.
