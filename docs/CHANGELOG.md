# Cognix Nexus — Changelog

## 2026-10-13
- Recorded Release Gates run #38344416584 and provider job #115122415177 as PASS on revision c354aa1804a1ef473eb091bdfca45a9532eb2e8a; Google Drive returned a folder reference with no provider probe failures.
- Recorded passing Supabase Storage, B2, Cloudinary, tiered storage, extraction, Cohere 1536 embedding, RRF/RAG/citation and owner-isolation checks.
- Documented optional Gemini 401, Hugging Face 400, Groq 429 and Cloudflare 410 route diagnostics and retained skipped browser, Book, Sentry and recovery gates as pending.
- PR #39 safety follow-up separates Book synthetic acceptance from production DB and adds recovery target isolation preflight; not yet merged or runtime-verified.


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
