# Cognix Nexus — Current State

## Latest verified update — 2026-10-14 00:55+06:30 (supersedes older status below)

- **Phase 13–21 AI runtime implementation complete (all local commits pending push):**

  | Commit | Phase | Tests | Key files |
  |---|---|---|---|
  | `e1bf06c` | Ph13 — AI Active Layer | 34/34 | `agent.py`, `brain_agent.py`, `034_*.sql`, `test_phase13_runtime.py` |
  | `93c6a46` | Ph14 — Learning Science | 32/32 | `learning_science_service.py`, `learning_science.py`, `035_*.sql`, `test_phase14_*.py` |
  | `a542be3` | Ph15 — Life Integration | 27/27 | `life_integration_service.py`, `life_integration.py`, `036_*.sql`, `test_phase15_*.py` |
  | `3dc74b4` | Ph16 — Advanced Layer | 37/37 | `advanced_layer_service.py`, `advanced_layer.py`, `037_*.sql`, `test_phase16_*.py` |
  | `df09ee7` | Ph17 — Core Integration | 42/42 | `core_integration_service.py`, `core_integration.py`, `038_*.sql`, `test_phase17_*.py` |
  | `3fbacad` | Ph18/19 — Media Boundary + Native UX | 29/29 | `media_boundary_service.py`, `media_boundary.py`, `039_*.sql`, `test_phase18_19_*.py` |
  | `ce38983` | Ph20/21 — Release Evidence + Readiness | 42/42 | `release_evidence_service.py`, `release_evidence.py`, `040_*.sql`, `test_phase20_21_*.py` |

  **Total: 243/243 tests passing locally across all phases.**

  All phases follow: RLS initplan-safe pattern, fail-closed service functions, psycopg-stubbed tests, owner-isolated routers registered in `main.py`, and SQL migrations 034–040.


## Previous update — 2026-10-13 21:00+06:30

- Latest `main` revision checked: `66a2d8b45b17df02640d4615a5f9aabca41067e2`. Cognix Core CI [#38414102418](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38414102418) and CodeQL [#38414102026](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38414102026) both completed successfully.
- **New local commit `e3fc567` (pending push):** P0 release gate expansion — 11 files changed, 1230 insertions:
  - `e2e/authenticated-smoke.spec.ts` — expanded from 1 test to 30+ tests covering all 24 pages, API `/health` + `/ready`, accessibility landmarks, unauthenticated redirects
  - `e2e/accessibility.spec.ts` — new: WCAG AA axe-core sweep on all authenticated pages + keyboard navigation checks (requires `@axe-core/playwright`)
  - `scripts/render_health_check.py` — new: external Render `/health` + `/ready` check with response timing and env-var presence inventory (values never printed); `--compare-env-vars` flag for blueprint diff
  - `scripts/lighthouse_check.py` — new: Lighthouse performance/accessibility baseline runner (fails if accessibility < 0.9 or performance < 0.5)
  - `scripts/book_acceptance_contract.py` — extended: added column presence checks for `lesson_packs`, `derived_books`, `chapter_summaries`, `book_summaries`, `reading_events`
  - `.github/workflows/release-gates.yml` — added `render-health` CI job triggered by `run_render_health` boolean input; uses `COGNIX_API_BASE_URL` secret
- Render API/worker: internal `/health` HTTP 200 confirmed; external `/ready` still unverified (requires `COGNIX_API_BASE_URL` secret in GitHub + manual or CI run of `render-health` job)
- Provider E2E [#38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584) passed; Sentry, recovery, Book contract, browser smoke, GDPR, accessibility, performance, mobile remain pending.



> Owner: Release/status tracking
> Update when: status, evidence, gate, blocker, deferral, or next action changes
> Last Updated: 2026-10-13
> Do NOT put here: architecture specifications, full design-system rules, historical source documents, or unverified claims presented as facts.

## 1. Current Release

Release-candidate / pre-final-production-verification. Final production smoke and release approval are still blocked by external gates and configuration reconciliation.

## 2. Current Phase

P0 engineering verification → provider/storage/Book acceptance → authenticated browser → recovery/GDPR/observability/accessibility/performance/mobile → grouped manual verification → final production smoke → release approval.

Future Phase 13–21 runtime activation remains blocked until the current release guard is satisfied.

## 3. Overall Status

- **Latest main CI/security checks:** Cognix Core CI [38225351392](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38225351392) and CodeQL [38225351317](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38225351317) both PASS on merge commit `c711aa225e7306d1b8b637e241abc05116167b01` (2026-10-12). CI frontend, backend, and mobile jobs passed; both Python and JavaScript/TypeScript CodeQL analyses passed.

- **AI routing code:** provider endpoints and model IDs are code-defined; LLM routes are enabled by provider-key presence. Live `public.embeddings.embedding_vector` is `vector(1536)` (101 non-null rows at the 2026-10-11 audit); a separate JSONB `embedding` column also exists. Cohere is currently the only embedding route compatible with the persisted vector dimension.
- **Render deployment:** API deploy `dep-db6ac8uk1f9s73f4eaf0` and Worker deploy `dep-db6ac8uk1f9s73f4eb7g` are live on commit `c643ff6fa399e5d9722a84ffd87c5d94b56a7af4` (2026-10-12). The commit adds safe Google Drive HTTP-status diagnostics.

- **Render configuration:** Live API `Cognix-Core` and Worker `cognix-core-worker-runtime` both report Python runtime, rootDir `web-platform/backend`, build command `pip install -r requirements.lock`, expected start commands, `/health` configured, and commit-triggered auto-deploy. Direct HTTP verification from the connected environment is unavailable; API `/health`, API `/ready`, and post-deploy worker health are not marked PASS without a response/log proving them.

- **Render environment audit:** `render.yaml` declares the expected API/worker variable names, including Google OAuth variables. The connected Render integration cannot enumerate live environment variable names, so blueprint-to-live comparison is still unverified; no variables were deleted or overwritten.
- **Google Drive OAuth / export:** Provider E2E runs [#38231060560](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38231060560) and [#38259902309](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38259902309) both fail only at Google Drive with `GoogleDriveFolderNotFoundOrInaccessible:HTTP_404`; latest job [#114847495973](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38259902309/job/114847495973) confirms the workflow receives masked Google OAuth variables and `COGNIX_DRIVE_PROVIDER=google`. Owner has confirmed `GOOGLE_DRIVE_ROOT_FOLDER_ID` and `GOOGLE_REFRESH_TOKEN` were repeatedly checked. Code inspection found the app requests only `drive.file` while using a user-supplied existing root-folder ID, which may be inaccessible under that scope. Proposed branch `fix/google-drive-root-folder-scope` changes to full Drive scope; this is a broader sensitive scope and requires owner consent/re-authorization after review/merge. This is a hypothesis-based code correction, not yet proven by a successful API call. Runtime acceptance remains FAIL until a real export and idempotency retry pass.
- **Database migration head:** live Supabase migration history and advisor were re-verified on 2026-10-12 at `033_rls_policy_initplan_indexes` (version `20261012034910`). The seven owner-policy `auth_rls_initplan` findings and the unindexed `knowledge_items.chapter_id` FK finding are no longer reported. Remaining performance notices are INFO-level unused-index findings; Supabase Auth still warns that leaked-password protection is disabled.

External production gates remain pending until fresh evidence is captured. CI PASS and a live deployment do not equal release PASS. Supabase Auth leaked-password protection remains disabled because the current Free plan does not permit enabling it, per owner report; track as a documented plan limitation rather than a completed security control.

## 4. COMPLETED / CODE-READY

- Book Intelligence Phase 1–6 implementation and Phase 7–12 Knowledge Vault/review/synthesis foundations.
- Durable AI reading checkpoint/retry/backoff/provider-event audit foundations.
- Knowledge Vault UI/API foundation.
- Supabase migrations 031–033 are present in the repository; live migration head 033 and related advisor results were verified 2026-10-12.
- Cloudinary upload/read/checksum/delete round-trip was previously observed.
- Google Drive OAuth/export implementation and idempotent upsert path.
- Provider E2E harness for provider, extraction, embedding, retrieval/citation and storage checks.
- Security overrides and CodeQL workflow.
- Phase 13–21 deterministic contracts, preparation plans, activation matrix/manifest and test coverage; these do not activate future runtime.
- Provider-key-only LLM routing and fixed 1536-dimension production embedding compatibility refactor merged as commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae`.
- CI and CodeQL succeeded on that commit.
- API and worker deploys for that commit were observed live at the time checked.

## 5. VERIFIED EVIDENCE

- Current main CI run [38201410726](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38201410726): success on `4805506ab1e82b5114850b5a40aebdcd2be21047`.
- Current main CodeQL run [38201410735](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38201410735): success on the same commit.
- Render API deploy `dep-db65gorbc2fs739bk7i0` and Worker deploy `dep-db65gorbc2fs739bk6s0`: live on app commit `5be9d641da6972fdfb0d4498afd44c42fbf9705a` on 2026-10-12.
- Cloudinary live round-trip: previously verified; re-run if required by the current release evidence policy.
- Repository/live Supabase migration head `033_rls_policy_initplan_indexes`: re-verified 2026-10-12; targeted performance-advisor findings are resolved.
- Previous four-item VERIFY close-out (migration head, worker deployment policy, Secret Vault KDF, R2 role) was recorded on 2026-10-08. Current live Worker auto-deploy trigger now reports `commit`, matching `render.yaml`.

## 6. PENDING — CURRENT RELEASE

1. API runtime mismatch is resolved in live Render metadata and both services deployed application commit `5be9d64`. Obtain direct API `/health`, `/ready`, and worker health evidence before calling readiness fully verified.
2. Inventory actual live Render environment-variable names and compare with the current code/blueprint. Remove only verified obsolete overrides; preserve API keys, database, auth, storage, Google, release-gate and test variables. The connected Render action cannot currently enumerate or delete individual variables.
3. Migration 033 and targeted advisor findings are verified. Enable and verify Supabase Auth leaked-password protection, then capture a fresh database readiness check.
4. Provider E2E [#38231060560](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38231060560) preflight PASS / provider E2E FAIL. Supabase/B2/Cloudinary storage, extraction, RAG/citation, owner isolation, Cohere 1536 embeddings and healthy OpenRouter/Mistral/Cohere/Groq routes passed. Optional Gemini 401, Hugging Face 400, and Cloudflare 410 are diagnostic. The only blocking probe is Google Drive HTTP 404: `GoogleDriveFolderNotFoundOrInaccessible`. Verify `GOOGLE_DRIVE_ROOT_FOLDER_ID` is the ID of the intended folder and share that folder with the Google account represented by the Actions OAuth credentials; do not assume a Render refresh-token update also changed GitHub Actions secrets.
5. Google Drive export/idempotency drill remains blocked by HTTP 404. Verify the GitHub Actions secret `GOOGLE_DRIVE_ROOT_FOLDER_ID` and folder access for the OAuth account used by the workflow; only regenerate OAuth credentials if later evidence indicates an auth failure.
6. Supabase Storage write/read/checksum passed in provider E2E #38046919712; rerun if fresh release evidence is required.
7. Backblaze B2 >50 MB write/read/checksum passed in provider E2E #38046919712; rerun if fresh release evidence is required.
8. Run controlled Book Intelligence 9-category / 170-file dry-run, duplicate fingerprint E2E, checkpoint/resume, durable ledger, distillation/lesson packs/derived-book lineage and export acceptance.
9. Run authenticated Playwright production smoke.
10. Run mobile EAS/device smoke.
11. Complete WCAG keyboard/screen-reader/responsive sweep.
12. Capture Lighthouse/performance baseline.
13. Run production backup → isolated restore → rollback drill.
14. Complete GDPR owner-data export/delete drill and cleanup.
15. Verify Sentry live ingestion.
16. Complete P1 UI state normalization and grouped manual verification **last**.
17. Run final production smoke against the intended revision and obtain release approval before tagging.

## 7. BLOCKED

- Final production smoke and release/tag until required gates have evidence-backed PASS. Provider E2E #38046919712 failed, so browser-smoke, recovery-drill, sentry-probe, and book-contract jobs were skipped.
- Phase 13–21 production runtime activation until release approval and each phase's own activation evidence.

## 8. DEFERRED

- Paid LLM activation.
- Google Drive re-authorization/account-owner consent until the owner performs the external authorization step.
- Future-phase autonomous/native/device runtime until the release guard is satisfied.

Deferred items are not reported as completed.

## 9. NEXT ACTION ORDER

1. Render API and Worker settings now match the intended Python/root/build/start/health/commit-triggered configuration. Verify live health/readiness and safely inventory actual environment-variable names; the connected Render integration cannot enumerate/delete individual environment variables.
2. Verify the GitHub Actions Google Drive root-folder ID and folder permission against the OAuth account, then rerun Release Gates with `run_provider_e2e=true`; retain the HTTP 404 evidence until a successful real export/idempotency result is recorded.
3. Run provider/storage/Book acceptance using production-safe credentials and capture revision/time/result/cleanup evidence.
4. Run authenticated browser and remaining external gates.
5. Complete grouped manual verification last.
6. Run final production smoke and obtain release approval.
7. Only after release approval, activate Phase 13, then 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 one phase at a time.

## 10. EVIDENCE RULE

Static code, prepared contracts, configured secrets, or a live deployment are not production PASS by themselves. Record only observed results, include the revision and cleanup status, and never record secret values.
