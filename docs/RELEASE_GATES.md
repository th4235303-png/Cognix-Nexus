## Reconciled gate status — 2026-10-14

The main revision inspected is `ea010485390c82bed48853c8433802fdf30cab1a`. No combined commit-status records were returned for that exact revision; prior PASS runs on older commits do not establish current-head CI/CodeQL PASS.

Phase 13–21 runtime code is in main and repository docs report 243/243 local tests, but the tests use stubbed database paths. Migrations 034–040 are not proven applied to production. The release remains BLOCKED until current-head CI/CodeQL and isolated real-PostgreSQL migration/RLS tests pass.

**Known gate implementation issue:** `scripts/render_health_check.py --compare-env-vars` currently compares `os.getenv()` in the process running the script. In GitHub Actions that is the runner environment, not the live Render service configuration. Do not use this result as proof of live Render parity until the script reads the authorized Render service configuration, redacts values, and has tests proving the source of its inventory.

Use [the reconciled execution plan](EXECUTION_PLAN_2026-10-14.md) for the authoritative run order. Browser tests skipped for missing credentials, synthetic Book contracts, evidence rows, and CI's ephemeral PostgreSQL restore are not production PASS.

---

# Cognix Nexus — Release Gate Matrix

## Latest verified evidence — 2026-10-13 (supplements older evidence below)

- Latest `main` revision checked: `66a2d8b45b17df02640d4615a5f9aabca41067e2`; Cognix Core CI [#38414102418](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38414102418) and CodeQL [#38414102026](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38414102026) both PASS. CI's Book synthetic contract and ephemeral PostgreSQL restore drill passed, but neither is evidence of real production-account acceptance or recovery.
- Owner reports `chore/prune-unverified-ai-providers` deleted. The branch's stale changes were reviewed and intentionally not merged. No open PRs were returned by the repository query.
- Render API/worker metadata matches the checked-in blueprint and both services are active. API logs show repeated internal `/health` HTTP 200 responses; worker startup logged PostgreSQL persistence configured. External `/ready` response and live environment-variable-name inventory remain unverified.

- [Release Gates run #38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584), provider job [#115122415177](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584/job/115122415177): provider E2E PASS on revision `c354aa1804a1ef473eb091bdfca45a9532eb2e8a`; Google Drive returned a folder reference and `provider_probe_failures: []`.
- Supabase Storage, B2, Cloudinary, tiered storage, extraction, Cohere 1536 embedding, RRF/RAG/citation and owner isolation passed. Optional Gemini 401, Hugging Face 400, Groq 429 and Cloudflare 410 are nonblocking unless those routes are required.
- Sentry, recovery, Book contract and browser smoke were skipped; they remain pending.
- PR #39 safety guardrails are merged as `3cb9bea49bfc207691c1289329c95a4746c332ba`. Post-merge Cognix Core CI [#38410040713](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38410040713) and CodeQL [#38410040961](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38410040961) passed on `main` revision `902ad74ca58f0c52edd3b72bddfbe698390db0d7`; frontend/backend/mobile and both CodeQL analyses passed. The CI restore drill uses an ephemeral PostgreSQL service container, not the real production recovery target.
- PR #40's Media Intelligence source-monitoring plan is also merged on that revision and remains planning-only, not an implemented feature. Real authenticated browser smoke, Sentry ingestion, production backup/restore, and the other operator/device gates remain separate release gates.
- Recovery guard requires a distinct target DSN plus repository variable `COGNIX_RECOVERY_TARGET_ISOLATED=true`; this declaration does not itself prove target isolation or cleanup. Do not run the real recovery drill until target identity and cleanup/rollback are explicitly confirmed.


> Owner: Release engineering
> Last Updated: 2026-10-13
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
- The connected Render integration cannot enumerate/delete individual environment variables. Provider E2E runs [#38231060560](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38231060560) and [#38259902309](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38259902309) failed only at Google Drive with `GoogleDriveFolderNotFoundOrInaccessible:HTTP_404`; latest job confirms `COGNIX_DRIVE_PROVIDER=google` and masked OAuth variables are injected. Owner confirms `GOOGLE_DRIVE_ROOT_FOLDER_ID` and `GOOGLE_REFRESH_TOKEN` were checked repeatedly. Code uses `drive.file` while targeting a pre-existing owner-provided root folder; proposed branch `fix/google-drive-root-folder-scope` changes to full Drive scope because `drive.file` may not grant access to arbitrary existing folders. Full Drive scope is broader/sensitive and requires explicit owner review and fresh OAuth consent after merge. This is a code-based hypothesis, not proven until the real export and idempotency retry pass. Preserve secret values.
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
