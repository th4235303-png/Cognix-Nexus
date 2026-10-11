# Cognix Nexus — Deployment

> Owner: Deployment/release operations
> Update when: hosting, deployment configuration, environment requirements, or rollback procedure changes
> Last Updated: 2026-10-11
> Do NOT put here: product roadmap or live evidence tables.

## Production targets
- Frontend: Netlify.
- API: Render.
- Worker: Render.
- Database/Auth: Supabase/PostgreSQL.
- Storage: Cloudinary + Supabase Storage + B2, with Google Drive for user-owned export/backup.

Current live service identities are `Cognix-Core` (`srv-dauh0tu0tbcc73fdds2g`) and `cognix-core-worker-runtime` (`srv-dav13vm0tbcc73d4ek8g`). The intended repository layout is Python under `web-platform/backend`, installed from `requirements.lock`; the API serves `/health` and `/ready`, and the worker exposes `/health` while processing the queue. The checked-in blueprint has been prepared to use these service identities and this repository layout, with commit-triggered deployment for both services to prevent API/worker revision skew. **The live Render settings are not yet reconciled**: API metadata still reports `runtime=node`, `rootDir=backend`, and `requirements.txt`; worker metadata reports blank `rootDir`, an inline `cd web-platform/backend` command, and auto-deploy off. Do not merge/apply this blueprint change until the live API is changed to Python + `web-platform/backend` + `requirements.lock`; otherwise the API's automatic deployment on merge could fail. The connected Render tools can inspect services and trigger deploys but cannot update runtime/root/build/deploy-policy settings.

## Release sequence
1. CI green on main.
2. Apply/verify database migrations.
3. Deploy API and worker from intended main revision.
4. Verify /health and /ready.
5. Verify worker queue/logs.
6. Run provider/storage smoke tests.
7. Run frontend production smoke.
8. Reconcile release evidence.
9. Only then promote/tag the release.

## Required production configuration
Keep required database/auth/JWKS/CORS/host configuration, provider credentials, Google OAuth/Drive values, storage credentials/settings, E2E/recovery/release-gate variables, and optional Sentry DSN as appropriate for each service. AI endpoints and model IDs are code-defined; do not configure provider model or URL overrides. `COHERE_API_KEY` is currently required for the AI release-gate preflight because production vectors use dimension 1536. Secrets are backend-only and never committed.

## Google Drive
OAuth/export implementation exists. Real account consent, refresh-token issuance and export verification remain pending/deferred until the account owner performs the activation drill.

## Netlify
The frontend build is rooted at web-platform/frontend. Production deployment must use the intended main revision and pass UI smoke/release gates.

## Rollback
Stop promotion first. Keep the last known-good application revision available. Verify database compatibility before application rollback. Never assume a destructive database rollback is safe; prefer forward-compatible migrations or an isolated restore drill.

## Environment-variable cleanup
Do not delete variables based only on a guessed naming pattern. Compare the actual live names against code, workflows, `render.yaml` and test/recovery procedures. Remove only verified-unused model/URL/legacy routing overrides. Never replace the whole environment unless every retained variable has been inventoried and verified. Record the cleanup and restart/deploy evidence.

## External activation
Storage, Drive, AI and monitoring activation procedures are in `docs/STORAGE.md` and `docs/runbooks/external-activation.md`.
