# Cognix Nexus — Changelog

## 2026-10-13
- Recorded Release Gates run #38344416584 and provider-e2e job #115122415177 as PASS on checkout revision c354aa1804a1ef473eb091bdfca45a9532eb2e8a.
- Closed the previous Google Drive HTTP 404 provider E2E blocker for this run: Google Drive returned a folder reference and `provider_probe_failures` was empty.
- Recorded successful Supabase Storage, Backblaze B2, Cloudinary, tiered-storage, extraction, Cohere 1536-dimensional embedding, RRF/RAG/citation, and owner-isolation checks.
- Documented optional Gemini 401, Hugging Face 400, Groq 429, and Cloudflare 410 route diagnostics; OpenRouter, Mistral, and Cohere routes succeeded.
- Kept Sentry, recovery, Book contract, browser smoke, Render live health/environment inventory, mobile, accessibility, performance, GDPR, grouped manual verification, and final release approval pending because they are unverified or skipped.

## 2026-10-11
- Recorded current main CI PASS (run 38071211914) and CodeQL PASS (run 38071211816) for commit 538520aa908c8fdadef0a38c7fba23fea8ca3fae.
- Recorded live Render API and worker deploy evidence for that commit, while explicitly tracking live-vs-blueprint configuration drift and unverified environment-variable cleanup.
- Updated release status and roadmap to keep external provider/storage/Book/browser/device/accessibility/performance/recovery/GDPR/observability/manual gates pending until evidence is captured.
- Reconciled provider setup instructions with provider-key-only LLM routing and the persisted vector(1536) embedding schema.

## 2026-10-08
- Closed the four explicit VERIFY items with evidence: migration head 032, live Render worker deployment policy manual/off, Secret Vault PBKDF2-SHA256 600k implementation, and R2 non-production role.
- Added release-gate preflight and Book Intelligence acceptance contracts.
- Added authenticated Playwright smoke configuration and login accessibility fixes.
- Added Phase 13–21 non-runtime foundations, lifecycle/media/release-evidence contracts and deterministic contract tests.
- Added future-phase preparation plans and activation matrix.
- Reconciled roadmap/docs to distinguish static readiness from real production PASS.
