# Cognix Nexus — Release Gate Matrix

> Owner: Release engineering  
> Last Updated: 2026-10-13  
> Secrets and secret values never belong in this file.

This file defines automated gates and gates requiring operator/browser/device evidence. A skipped job is not a PASS.

## Automated / Code-Ready

| Gate | Runner | Operator input / evidence |
|---|---|---|
| AI + embeddings + extraction + RRF/citation | `scripts/provider_e2e.py` | Cohere API key required for persisted 1536-dimensional embeddings; at least one configured LLM route must succeed. |
| Supabase Storage | `scripts/provider_e2e.py` | Supabase URL/service-role + bucket; write/read/cleanup passed in run #38344416584. |
| Backblaze B2 | `scripts/provider_e2e.py` | B2 credentials; tiered large-file path passed in run #38344416584. |
| Cloudinary | `scripts/provider_e2e.py` | Cloudinary credentials; upload/read/cleanup passed in run #38344416584. |
| Google Drive | `scripts/provider_e2e.py` | OAuth client + account-owner refresh token; actual provider E2E passed in run #38344416584. |
| Backup/restore | `scripts/backup_restore_drill.py` via `recovery-drill` | Requires a distinct `COGNIX_RECOVERY_TARGET_DATABASE_URL` and repository variable `COGNIX_RECOVERY_TARGET_ISOLATED=true` after operator verification; do not run until target isolation and cleanup/rollback are understood. Not run in #38344416584. |
| Book schema/lifecycle contract | `scripts/book_acceptance_contract.py` | Requires the dedicated `COGNIX_BOOK_ACCEPTANCE_DATABASE_URL` secret pointing to an isolated test/staging database; synthetic fixtures must never use production. Not run in #38344416584. |
| Sentry ingestion probe | `scripts/sentry_live_check.py` | Sentry DSN; not run in #38344416584; UI observation may remain manual. |
| Authenticated browser smoke | Playwright via `browser-smoke` | E2E base/API URL and test account; not run in #38344416584. |
| Frontend typecheck/lint/build | CI | See latest main CI evidence before release. |
| Backend compile/unit/integration | CI | See latest main CI evidence before release. |
| Mobile config validation | CI | CI validation does not replace device smoke. |

## Latest Provider Evidence

- Run [#38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584), job [provider-e2e #115122415177](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584/job/115122415177), started 2026-10-13 04:01 UTC, checkout revision `c354aa1804a1ef473eb091bdfca45a9532eb2e8a`.
- Result: `status: PASS`, `provider_probe_failures: []`; Google Drive returned a valid folder reference. Supabase Storage, B2, Cloudinary, tiered storage, extraction, Cohere 1536-dimensional embedding, RRF/RAG/citation, and owner isolation passed.
- Optional LLM route failures: Gemini HTTP 401, Hugging Face HTTP 400, Groq HTTP 429, Cloudflare HTTP 410. OpenRouter, Mistral, and Cohere succeeded. Treat those errors as route-specific diagnostics unless those providers are required for the intended release.
- Cleanup: Supabase test objects and Cloudinary test asset were deleted successfully in the job logs. B2 cleanup result is not explicitly summarized in the result object; do not claim cleanup for B2 unless its deletion log is confirmed.
- Preflight and provider-e2e jobs passed. Sentry, recovery, Book contract, and browser smoke were skipped because their dispatch inputs were not enabled.
- Safety follow-up in PR #39: Book synthetic acceptance now uses a dedicated isolated-database secret, not the production database URL. Recovery preflight now requires a different target DSN and explicit `COGNIX_RECOVERY_TARGET_ISOLATED=true`. These protections are code changes pending PR checks/merge; they are not runtime gate evidence.

## Additional Configuration / Security Checks

- `render.yaml` declares API `Cognix-Core` and worker `cognix-core-worker-runtime` with Python runtime, `web-platform/backend` root, locked requirements build, expected start commands, `/health` health check, and commit-triggered auto-deploy.
- Direct live API `/health`, API `/ready`, and post-deploy worker health responses are not yet recorded. Do not mark these PASS based on blueprint metadata alone.
- The connected Render integration cannot enumerate/delete individual live environment variables. Compare the live names through a supported dashboard/operator path before removing anything. Preserve keys, database, auth, storage, Google, release-gate, and test variables; do not delete by name pattern alone.
- Supabase migration `033_rls_policy_initplan_indexes` is live; the targeted RLS initplan and chapter foreign-key index findings were resolved in the 2026-10-12 audit. Supabase Auth leaked-password protection remains disabled per owner report that the current Free plan does not permit enabling it. Record this as a known limitation, not a completed control.
- Google Drive OAuth now uses the broader `https://www.googleapis.com/auth/drive` scope to support the configured existing root folder. Because this is a sensitive scope, retain only with explicit owner consent and applicable Google OAuth policy/verification requirements. The successful E2E run is evidence that the configured workflow currently works; it does not eliminate future token expiry/consent requirements.

## Operator / Browser / Device Gates — Pending

1. Authenticated Playwright production smoke.
2. Full keyboard/screen-reader/responsive sweep.
3. Lighthouse/performance baseline.
4. Mobile EAS/device smoke.
5. Production backup → checksum → isolated restore → rollback/cleanup drill.
6. GDPR owner-data export/delete and cleanup.
7. Sentry live ingestion probe.
8. Render API `/health` and `/ready`, worker health/runtime evidence, and live environment-name inventory.
9. Supabase Auth leaked-password protection: known current Free-plan limitation; revisit if plan/settings change.
10. Grouped manual UI verification, intentionally performed last.
11. Final production smoke and release approval/tag.

## Key Collection Order

Provide values only when needed for a specific gate. Never paste secrets into the repository.

1. AI/embedding provider keys.
2. Supabase service-role credentials.
3. B2 credentials.
4. Google OAuth values and account-owner refresh token.
5. Sentry DSN.
6. Browser E2E test account.
7. Production database + isolated recovery target DSN only for the final recovery drill.

Run `python scripts/release_gate_preflight.py` to identify runnable gates without printing values.

## Evidence Rule

A gate is PASS only when the real runner completes and records the revision, UTC timestamp, observed result, and cleanup status without secret values. Static code is READY, not PASS; skipped jobs remain pending.
