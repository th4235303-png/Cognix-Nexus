# Cognix Nexus — Changelog

## 2026-10-15
- Performed a fresh repository + infrastructure reconciliation across GitHub, Render, Supabase and Cloudflare.
- Reconciled hosting documentation: the active frontend service is currently Render `cognix-nexus-frontend`; no Vercel configuration/reference was found; Netlify is retained as legacy documentation only.
- Diagnosed the latest Render API deployment failure: `media_boundary.py` and `release_evidence.py` imported missing `get_current_owner_id` from `app.auth`.
- Fixed the auth dependency in main commit `40558ee3f6bed1c1d2dde79c80942754a6353534` so owner-isolated routers can resolve the authenticated owner and fail closed for anonymous requests.
- Recorded the required follow-up: deploy the fix to Render and capture `/health` + `/ready` evidence before release PASS.
- Verified Supabase `Cognix-Core` is healthy at migration `033_rls_policy_initplan_indexes`; leaked-password protection remains disabled and performance advisor findings are INFO-level unused indexes.
- Verified the connected Cloudflare account currently has no zones, Workers scripts or Pages projects; R2 is not enabled.
- Rewrote `CURRENT_STATE.md`, `ROADMAP.md`, `PROJECT_OVERVIEW.md`, `README.md`, `docs/DEPLOYMENT.md` and `docs/STORAGE.md` so release blockers and provider roles reflect observed infrastructure rather than stale historical evidence.

## 2026-10-14
- **Phase 13–21 AI runtime implementation complete** — 7 commits, 243/243 tests passing locally (psycopg-stubbed), pending push and Supabase migration apply.
  - Ph13 `e1bf06c`: AI Active Layer — `persist_lifecycle_event`, `persist_decision_record`, lifecycle events API, `034_*.sql` (RLS initplan-safe)
  - Ph14 `93c6a46`: Learning Science — `persist_learning_signal`, `persist_learning_path`, `035_*.sql`
  - Ph15 `a542be3`: Life Integration — `persist_restore_request`, `persist_consent_event`, `persist_capsule_ref`, `036_*.sql`
  - Ph16 `3dc74b4`: Advanced Layer — `persist_wiki_entity`, `persist_growth_metric`, `persist_offline_handoff`, `persist_secret_ref`, `037_*.sql`
  - Ph17 `df09ee7`: Core Integration — `persist_evidence_artifact`, `persist_document_classification`, `apply_document_lifecycle_transition`, `persist_parallel_text`, `038_*.sql`
  - Ph18/19 `3fbacad`: Media Boundary + Native UX — `persist_media_asset`, `persist_ocr_result`, `persist_device_gate`, `039_*.sql`
  - Ph20/21 `ce38983`: Release Evidence + Readiness — `persist_gate_evidence`, `persist_recovery_drill`, `evaluate_release_checklist`, `persist_release_decision`, `040_*.sql`
- Updated phase foundation/status documentation to reflect runtime implementation status.
- `app/main.py` registered media-boundary and release-evidence routers.

## 2026-10-13
- Recorded Release Gates run #38344416584 and provider job #115122415177 as PASS on revision `c354aa1804a1ef473eb091bdfca45a9532eb2e8a`; Google Drive returned a folder reference with no provider probe failures.
- Recorded passing Supabase Storage, B2, Cloudinary, tiered storage, extraction, Cohere 1536 embedding, RRF/RAG/citation and owner-isolation checks.
- Documented optional provider route diagnostics and retained skipped browser, Book, Sentry and recovery gates as pending.
- PR #39 safety follow-up separates Book synthetic acceptance from production DB and adds recovery target isolation preflight.

## 2026-10-11
- Recorded current main CI and CodeQL PASS for commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae`.
- Recorded live Render API and worker deploy evidence for that commit while tracking live-vs-blueprint configuration drift.
- Reconciled provider setup instructions with provider-key-only LLM routing and the persisted `vector(1536)` embedding schema.

## 2026-10-08
- Closed the four explicit VERIFY items with evidence: migration head 032, live Render worker deployment policy, Secret Vault PBKDF2-SHA256 600k implementation, and R2 non-production role.
- Added release-gate preflight and Book Intelligence acceptance contracts.
- Added authenticated Playwright smoke configuration and login accessibility fixes.
- Added Phase 13–21 non-runtime foundations, lifecycle/media/release-evidence contracts and deterministic contract tests.
- Added future-phase preparation plans and activation matrix.
- Reconciled roadmap/docs to distinguish static readiness from real production PASS evidence.
