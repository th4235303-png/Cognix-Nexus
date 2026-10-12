# Cognix Nexus — Current State

> Owner: Release/status tracking
> Update when: status, evidence, gate, blocker, deferral, or next action changes
> Last Updated: 2026-10-12
> Do NOT put here: architecture specifications, full design-system rules, historical source documents, or unverified claims presented as facts.

## 1. Current Release

Release-candidate / pre-final-production-verification. Final production smoke and release approval are still blocked by external gates and configuration reconciliation.

## 2. Current Phase

P0 engineering verification → provider/storage/Book acceptance → authenticated browser → recovery/GDPR/observability/accessibility/performance/mobile → grouped manual verification → final production smoke → release approval.

Future Phase 13–21 runtime activation remains blocked until the current release guard is satisfied.

## 3. Overall Status

- **Latest main CI/security checks:** Cognix Core CI [38201410726](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38201410726) and CodeQL [38201410735](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38201410735) both PASS on main commit `4805506ab1e82b5114850b5a40aebdcd2be21047` (2026-10-12). This commit is documentation-only; application code and Render deploys are on parent commit `5be9d641da6972fdfb0d4498afd44c42fbf9705a`. 
- **AI routing code:** provider endpoints and model IDs are code-defined; LLM routes are enabled by provider-key presence. Live `public.embeddings.embedding_vector` is `vector(1536)` (101 non-null rows at the 2026-10-11 audit); a separate JSONB `embedding` column also exists. Cohere is currently the only embedding route compatible with the persisted vector dimension.
- **Render deployment:** API deploy `dep-db65gorbc2fs739bk7i0` and Worker deploy `dep-db65gorbc2fs739bk6s0` are both `live` on application commit `5be9d641da6972fdfb0d4498afd44c42fbf9705a` (verified 2026-10-12). Both auto-deploy from `main` on commits.
- **Render configuration:** Live API `Cognix-Core` and Worker `cognix-core-worker-runtime` both report Python runtime, rootDir `web-platform/backend`, build command `pip install -r requirements.lock`, configured start commands, `/health`, and commit-triggered auto-deploy. This resolves the previously observed API `runtime=node` metadata mismatch. Direct `/health` and `/ready` HTTP verification was not obtainable in this session; no matching health-request logs were returned, so endpoint readiness is still unverified.
- **Render environment cleanup:** obsolete variable names have not been verified against the live service environment and have not been deleted. Do not infer that a variable is present from the blueprint alone.
- **Database migration head:** live Supabase migration history and advisor were re-verified on 2026-10-12 at `033_rls_policy_initplan_indexes` (version `20261012034910`). The seven owner-policy `auth_rls_initplan` findings and the unindexed `knowledge_items.chapter_id` FK finding are no longer reported. Remaining performance notices are INFO-level unused-index findings; Supabase Auth still warns that leaked-password protection is disabled.

External production gates remain pending until fresh evidence is captured. CI PASS and a live deployment do not equal release PASS.

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
4. Provider E2E [#38046919712](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38046919712) overall FAIL: Gemini 403, Hugging Face 400, Cerebras 402, Mistral 429, Cloudflare 1024 embedding RuntimeError, and expired/revoked Google refresh token. Storage, RAG/citation, owner isolation, and Cohere 1536-dimension probes passed. Reconcile optional provider model/access/quota configuration and retest without printing secrets.
5. Google Drive account-owner OAuth/refresh-token and real export/idempotency drill remains blocked until the owner re-authorizes and provides a valid refresh token.
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
2. Re-run release-gate preflight without printing secrets; the previous preflight passed, but provider E2E failed.
3. Run provider/storage/Book acceptance using production-safe credentials and capture revision/time/result/cleanup evidence.
4. Run authenticated browser and remaining external gates.
5. Complete grouped manual verification last.
6. Run final production smoke and obtain release approval.
7. Only after release approval, activate Phase 13, then 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 one phase at a time.

## 10. EVIDENCE RULE

Static code, prepared contracts, configured secrets, or a live deployment are not production PASS by themselves. Record only observed results, include the revision and cleanup status, and never record secret values.
