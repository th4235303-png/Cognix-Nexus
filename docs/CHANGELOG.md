# Cognix Nexus — Changelog

## 2026-10-14
- **Phase 13–21 AI runtime implementation complete** — 7 commits, 243/243 tests passing locally (psycopg-stubbed), pending push and Supabase migration apply.
  - Ph13 `e1bf06c`: AI Active Layer — `persist_lifecycle_event`, `persist_decision_record`, lifecycle events API, `034_*.sql` (RLS initplan-safe)
  - Ph14 `93c6a46`: Learning Science — `persist_learning_signal`, `persist_learning_path`, `035_*.sql`
  - Ph15 `a542be3`: Life Integration — `persist_restore_request`, `persist_consent_event`, `persist_capsule_ref`, `036_*.sql`
  - Ph16 `3dc74b4`: Advanced Layer — `persist_wiki_entity`, `persist_growth_metric`, `persist_offline_handoff`, `persist_secret_ref`, `037_*.sql`
  - Ph17 `df09ee7`: Core Integration — `persist_evidence_artifact`, `persist_document_classification`, `apply_document_lifecycle_transition`, `persist_parallel_text`, `038_*.sql`
  - Ph18/19 `3fbacad`: Media Boundary + Native UX — `persist_media_asset`, `persist_ocr_result`, `persist_device_gate`, `039_*.sql`
  - Ph20/21 `ce38983`: Release Evidence + Readiness — `persist_gate_evidence`, `persist_recovery_drill`, `evaluate_release_checklist`, `persist_release_decision`, `040_*.sql`
- Updated `docs/PHASE_15-21_FOUNDATION.md` (all 7 docs) and `CURRENT_STATE.md` to reflect runtime implemented status.
- `app/main.py` — registered `media_boundary.router` and `release_evidence.router`.

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
