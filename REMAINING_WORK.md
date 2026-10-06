# Cognix Nexus — Remaining Work

> Tactical execution tracker only.
> Strategic product scope: ROADMAP.md
> Production evidence: PRODUCTION_STATUS.md
> Stack/services: TOOLS.md
> UI specification: UI_PLAN.md
> UI implementation status: UI_STATUS.md

## Current verified state — 2026-10-06

| Area | State |
|---|---|
| Foundation / Brain Vault | 🟢 Implemented in main |
| Level Up 20 contracts | 🟢 Implemented foundation/contracts |
| Ownership / RLS | 🟢 Implemented; migration 028 applied in production |
| Worker leases / retry | 🟢 Implemented; CI integration green |
| SSRF hardening | 🟢 Implemented |
| CI | 🟢 Latest verified main CI #696 passed |
| Cloudinary | 🟢 Live round-trip verified |
| Supabase Storage | 🟡 Configured; full provider drill pending |
| Backblaze B2 | 🟡 Configured; full provider drill pending |
| Google Drive | 🟡 Integration implemented; real OAuth/provider drill awaits intentional credentials re-authorization |
| Paid LLM | ⚪ Deferred by product decision; do not block P0/UI work |
| Frontend | 🟡 Routes/components exist; completion/polish is the active workstream |
| Observability | 🟡 Code hooks exist; live ingestion not verified |
| Cloudflare edge | 🟡 Account exists; Cognix zone/edge deployment needs a domain |
| Account export/delete | 🔴 Full GDPR lifecycle not yet verified/closed |
| Production release | 🟡 Engineering gates are closing; final smoke/release remains |

## Priority 0 — Production verification

### P0.1 Live runtime
- [x] API/worker Render services are on the latest main revision (7287b682...).
- [ ] Verify /health and /ready with a reachable external probe (Render service is live; external probe tool cannot reach the onrender URL).
- [x] Verify production migration ledger through 028_rls_policy_dedup.sql.

### P0.2 Processing pipeline
- [ ] Re-run a fresh real book E2E with English + Myanmar + scanned pages.
- [x] Production DB snapshot confirms queued=0, running=0, 101 chunks, 101 embeddings, 1536-d vectors.
- [x] Hybrid RRF retrieval path is implemented and now owner-scoped; regression contract added.
- [ ] Verify the owner-scoped retrieval path against the live API with real provider credentials.
- [x] Verify 100+ chunks and 100+ embeddings on the production P0 test book (100/100; embeddings 1536-dim).
- [x] Confirm queued=0 and running=0; one historical failed task remains preserved for audit/retry verification.\n- [ ] Complete a fresh retry/recovery drill on a new production test job.

### P0.3 Source Inbox error matrix
- [ ] Normal HTML; Wikipedia; redirect; invalid URL; 403 fallback.
- [ ] 429 backoff; 5xx retry; timeout; non-HTML; oversized response.

### P0.4 Storage
- [ ] Supabase Storage private write/read/checksum.
- [ ] B2 large-file write/read/checksum.
- [ ] DB↔storage failure recovery.
- [ ] Crash/retry idempotency.
- [ ] Duplicate upload idempotency.

### P0.5 Vault
- [ ] Browser encrypt → ciphertext-only server storage.
- [ ] Logout/login/decrypt round-trip.
- [ ] Delete and server plaintext audit.

### P0.6 Google Drive
- [x] OAuth callback, refresh-token handling, export worker, folder creation, file upsert/idempotent retry code paths are implemented.
- [ ] Real Google OAuth callback/refresh-token drill with a user account.
- [ ] Real export worker upload/folder/file verification drill after credentials are re-authorized.

### P0.7 AI / RAG
- [x] Production DB contains 101 persisted embeddings and all observed vectors are 1536-dimensional.
- [x] RRF scoring is implemented in the production retrieval endpoint; owner scoping regression was hardened.
- [ ] Real provider embedding call and live API retrieval verification.
- [ ] Citation-backed LLM answer (paid LLM remains intentionally deferred).
- [ ] Unsupported question returns an evidence-safe response.
- [ ] Multi-book and contradictory-source behavior.
- Paid LLM activation is explicitly deferred and is not a P0 release blocker.

### P0.8 Authorization / RLS
- [x] Apply and verify migration 028.
- [x] Re-run Supabase performance/security advisors.
- [x] Redundant level-up deny-policy warnings are removed.
- [ ] Keep leaked-password-protection warning as an explicit external limitation until enabled.
- [x] Add regression coverage for owner-scoped hybrid retrieval/export/contradiction paths.
- [ ] Run full cross-user negative tests against the final deployed API release candidate.

### P0.9 Regression / release
- [x] Unit tests green in CI.
- [x] DB integration tests green in CI.
- [x] Backup/restore CI gate green in latest verified main run.
- [ ] Production-like Playwright E2E.
- [ ] Load/stress baseline.
- [ ] Rollback drill.
- [ ] Final production smoke.
- [ ] Release tag.

## P1 — UI completion / polish

Execution target: move from existing routes/components to a coherent, production-quality workspace. See UI_PLAN.md for design requirements and UI_STATUS.md for the live implementation checklist.

- [ ] Formal design tokens/component states.
- [ ] Dashboard hierarchy and responsive polish.
- [ ] Book upload/progress/filter + reader/TOC/highlight/note flow.
- [ ] Source Inbox error/retry states.
- [ ] Notes/backlinks/collections and graph exploration.
- [ ] RAG citation cards and evidence states.
- [ ] Review Center evidence/edit workflow.
- [ ] Vault unlock/auto-lock/client encryption states.
- [ ] Settings/provider/security surfaces.
- [ ] Level Up workspace polish.
- [ ] Vizora media/OCR/review polish.
- [ ] Export queue/history/retry polish.
- [ ] Keyboard/focus/ARIA/contrast/reduced-motion/WCAG AA.
- [ ] Authenticated Playwright smoke.
- [ ] Mobile Expo smoke/device evaluation.

## Product backlog after P1

These are not release blockers unless a specific release depends on them.

### AI / Learning
- [ ] Expand agent runtime beyond deterministic contracts.
- [ ] Real provider-backed synthesis/decision/writing/Feynman flows.
- [ ] Decay/interleaving/deep-research evaluation datasets.
- [ ] Evidence-bound agent TTL and retry evaluation.

### Life / Advanced
- [ ] Native capture/share sheet.
- [ ] Camera OCR and voice capture.
- [ ] Offline sync/device evaluation.
- [ ] JP/KR reading evaluation.
- [ ] Accessibility beyond the core WCAG gate.
- [ ] Legacy handoff operational drill.

### Vizora
- [ ] Rich vision provider integration.
- [ ] Batch media review.
- [ ] Media metadata/review UX.
- [ ] Drive package E2E.

### Infrastructure
- [ ] Production observability ingestion.
- [ ] Cloudflare zone/WAF/rate-limit deployment once a Cognix domain is available.
- [ ] Optional Redis/rate-limit/cache evaluation.
- [ ] Evaluation and stress-test suites.

## Documentation split

- PRODUCTION_STATUS.md — evidence and live gates only.
- REMAINING_WORK.md — tactical execution backlog only.
- ROADMAP.md — strategic product waves only.
- TOOLS.md — service catalog and provider ownership only.
- UI_PLAN.md — UI design/product requirements only.
- UI_STATUS.md — UI implementation/verification status only.
- ARCHITECTURE.md — system topology and boundaries.
- DATA_MODEL.md — tables, ownership and lineage.
- DEPLOYMENT.md — Render/Netlify/Supabase release runbook.
- PIPELINE.md — source/book processing lifecycle.
- AGENT.md — agent jobs/runs/findings/review contract.
- TROUBLESHOOTING.md — operational failures and recovery.
- DECISIONS.md — durable architecture decisions.
- CHANGELOG.md — release/change history.
- SECURITY.md — actual vulnerability-reporting/security policy.

## Execution rule

**Verify → implement/fix → test → production verify → update evidence → main.**

All implementation and documentation changes for this project land on **main**. Do not treat a feature as complete until the changed main revision is tested and its production evidence is updated.

## Known external limitations

- **Paid LLM:** intentionally deferred for now. Provider credentials/credits are not part of the current completion gate.
- **Supabase Leaked Password Protection:** currently disabled. The current project is on the free tier, so this account-level Auth feature cannot be enabled from the current plan. Keep the warning visible and do not mislabel it as a code defect.
- **Cloudflare:** no Cognix DNS zone/domain is available for edge deployment yet.

## Definition of Done — current release track

- P0 engineering gates are green or explicitly deferred by product decision.
- RLS/migration evidence is current.
- Storage and processing E2E evidence is current.
- Monitoring/backup/rollback evidence exists where available.
- Frontend production smoke and UI completion are green.
- Documentation reflects the verified state.
- CI remains green on main.

## Change Log

| Date | Change |
|---|---|
| 2026-10-06 | Hardened hybrid RRF retrieval, Brain Vault export, and contradiction review/candidate paths with explicit owner scoping; added regression contract coverage; reconciled live DB evidence (101 chunks/embeddings, 1536-d vectors, queued/running zero). |
| 2026-10-06 | Reconciled tactical work with production evidence; removed paid LLM as a P0 blocker; added explicit free-tier leaked-password limitation; made main-only execution rule explicit; separated UI status from UI specification. |