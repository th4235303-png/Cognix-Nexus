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

Current live service identities are `Cognix-Core` (`srv-dauh0tu0tbcc73fdds2g`) and `cognix-core-worker-runtime` (`srv-dav13vm0tbcc73d4ek8g`). On 2026-10-11, both were observed deployed from commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae`; API deploy policy is commit-triggered, worker deploy policy is manual/off. The checked-in `render.yaml` currently declares different service names/root directories and a commit-triggered worker. This is unresolved drift: reconcile the blueprint and live settings in a separate, reviewed operation; do not blindly apply a sync that could change service behavior.

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
