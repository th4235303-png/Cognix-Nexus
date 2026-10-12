# Cognix Nexus — Release Gate Matrix

> Owner: Release engineering
> Last Updated: 2026-10-12
> Secrets and secret values never belong in this file.

This file defines what can be automated now and what still requires an operator/browser/device.

## Automated / code-ready

| Gate | Runner | Operator input |
|---|---|---|
| AI + embeddings + extraction + RRF/citation | `scripts/provider_e2e.py` | `COHERE_API_KEY` is required by current preflight for production-compatible 1536-dimensional embeddings. The gate requires at least one configured LLM route to succeed; individual optional LLM route errors are diagnostic when another route is healthy. A configured Cohere 1536-dimension embedding failure remains blocking. Alternate 1024-dimensional embedding probes are diagnostic only because they cannot write to persisted `vector(1536)` schema. |
| Supabase Storage | `scripts/provider_e2e.py` | Supabase URL/service-role + bucket |
| Backblaze B2 | `scripts/provider_e2e.py` | B2 credentials |
| Cloudinary | `scripts/provider_e2e.py` | Cloudinary cloud name + API key/secret |
| Google Drive | `scripts/provider_e2e.py` | OAuth client + account-owner refresh token; workflow explicitly forces the real Google provider |
| Backup/restore | `scripts/backup_restore_drill.py` via `recovery-drill` | production DATABASE_URL + isolated recovery target DSN |
| Book schema/lifecycle contract | `scripts/book_acceptance_contract.py` | test/staging DATABASE_URL |
| Sentry ingestion probe | `scripts/sentry_live_check.py` | Sentry DSN; UI observation remains manual |
| Frontend typecheck/lint/build | CI | none |
| Backend compile/unit/integration | CI | none |
| Mobile config validation | CI | none |

## Additional configuration checks

- Live Render API (`Cognix-Core`) and Worker (`cognix-core-worker-runtime`) both deployed successfully on `c711aa225e7306d1b8b637e241abc05116167b01`; runtime, root/build/start commands, `/health` configuration, and commit-triggered auto-deploy match the blueprint. Direct `/health`, `/ready`, and post-deploy worker health responses are still unverified because the connected runtime cannot fetch the service URLs and no matching fresh request logs were returned.
- The connected Render integration cannot enumerate/delete individual environment variables. The owner reports that Google OAuth was re-authorized and a new `GOOGLE_REFRESH_TOKEN` entered in Render; this does not update GitHub Actions secrets. The fresh Actions provider E2E run [#38231060560](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38231060560) failed only at Google Drive with `GoogleDriveFolderNotFoundOrInaccessible:HTTP_404`. Verify the GitHub Actions secret `GOOGLE_DRIVE_ROOT_FOLDER_ID` is the intended folder ID and that the OAuth account represented by the Actions client/refresh-token credentials has access to that folder. HTTP 404 can mean not found or inaccessible; do not claim which without checking. Preserve all other variables and never expose secret values. Gate remains FAIL until a real export and idempotency retry pass.
- Supabase migration `033_rls_policy_initplan_indexes` is live. The targeted RLS initplan and chapter foreign-key index findings are resolved. Supabase Auth leaked-password protection remains disabled; owner reports it cannot be enabled on the current Free plan, so record this as an explicit plan limitation rather than repeatedly requesting the same action.

## Operator/browser/device gates — intentionally last

These are not promoted to PASS from static code inspection:

1. Supabase Auth leaked-password protection is a known limitation on the current Free plan; verify only if plan/settings change.
2. Authenticated Playwright production smoke.
3. Full keyboard/screen-reader/responsive sweep.
4. Lighthouse/performance baseline.
5. Mobile EAS/device smoke.
6. Production backup/restore/rollback against the real environment.
7. GDPR export/delete against a real owner account.
8. Sentry live event ingestion.
9. Final production smoke and release approval.

## Key collection order

Provide values only when requested for a specific gate. Never paste them into the repository.

1. AI/embedding provider keys.
2. Supabase service-role credentials.
3. B2 credentials.
4. Google OAuth values and account-owner refresh token.
5. Sentry DSN.
6. Browser E2E test account.
7. Production DATABASE_URL + isolated recovery target DSN only for the final recovery drill.

A preflight can be run first to show exactly which gate is runnable without printing values:
`python scripts/release_gate_preflight.py`.

## Evidence rule

A gate is PASS only when the real runner completes successfully and records:
- UTC timestamp
- revision
- gate name
- observed result
- cleanup result
- no secret values

Static code presence is READY, not PASS.
