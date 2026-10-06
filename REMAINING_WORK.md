# Cognix Nexus — Remaining Work

> Tactical execution tracker only.
> Strategic product scope: ROADMAP.md
> Production evidence: PRODUCTION_STATUS.md
> Stack/services: TOOLS.md
> UI roadmap: UI_PLAN.md

## Current verified state — 2026-10-06

| Area | State |
|---|---|
| Foundation / Brain Vault | 🟢 Implemented in main |
| Level Up 20 contracts | 🟢 Implemented foundation/contracts |
| Ownership / RLS | 🟢 Implemented; policy cleanup pending |
| Worker leases / retry | 🟢 Implemented; CI integration green |
| SSRF hardening | 🟢 Implemented |
| CI | 🟢 Latest main run #696 passed |
| Cloudinary | 🟢 Live round-trip verified |
| Supabase Storage | 🟡 Configured; full provider drill pending |
| Backblaze B2 | 🟡 Configured; full provider drill pending |
| Google Drive | 🔴 Live OAuth/provider drill blocked |
| Paid LLM | 🔴 Live provider drill blocked by provider configuration/402 |
| Frontend | 🟡 Real routes/components exist; production activation remains paused |
| Observability | 🟡 Code hooks exist; live ingestion not verified |
| Cloudflare edge | 🟡 Account exists; Cognix zone/edge deployment not verified |
| Account export/delete | 🔴 Full GDPR lifecycle not yet verified/closed |
| Production release | 🔴 Not closed |

## Priority 0 — Production verification

### P0.1 Live runtime
- [ ] Verify API /api/v1/health and /ready against the current Render deploy.
- [ ] Verify worker is running the latest intended main revision.
- [ ] Verify production migration ledger through 028_rls_policy_dedup.sql.

### P0.2 Processing pipeline
- [ ] Re-run real book E2E with English + Myanmar + scanned pages.
- [ ] Verify queued → extraction → chapters → chunks → embeddings → retrieval/RRF.
- [ ] Verify 100+ chunks and 100+ embeddings on the production test book.
- [ ] Verify failed/queued retry behavior and cleanup.

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
- [ ] Re-authorize OAuth with the exact production Drive scope.
- [ ] Callback/refresh-token flow.
- [ ] Export worker upload and folder structure.
- [ ] File verification and idempotent retry.
- [ ] Remove live invalid_scope blocker.

### P0.7 AI / RAG
- [ ] Resolve live LLM 402/configuration blocker.
- [ ] Real embedding call and 1536-dimension verification.
- [ ] RRF score from the production retrieval path, not a hand-calculated substitute.
- [ ] Citation-backed answer.
- [ ] Unsupported question returns an evidence-safe response.
- [ ] Multi-book and contradictory-source behavior.

### P0.8 Authorization / RLS
- [ ] Apply and verify migration 028.
- [ ] Re-run Supabase performance/security advisors.
- [ ] Confirm redundant policy warnings are removed.
- [ ] Keep leaked-password-protection warning as an explicit external security action until enabled.
- [ ] Re-run cross-user negative tests.

### P0.9 Regression / release
- [x] Unit tests green in CI.
- [x] DB integration tests green in CI.
- [x] Backup/restore CI gate green in latest main run.
- [ ] Production-like Playwright E2E.
- [ ] Load/stress baseline.
- [ ] Rollback drill.
- [ ] Final production smoke.
- [ ] Release tag.

## Product backlog after P0

These are not production blockers unless a specific release depends on them.

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
- [ ] Accessibility and responsive polish.
- [ ] Legacy handoff operational drill.

### Vizora
- [ ] Rich vision provider integration.
- [ ] Batch media review.
- [ ] Media metadata/review UX.
- [ ] Drive package E2E.

### Infrastructure
- [ ] Production observability ingestion.
- [ ] Cloudflare zone/WAF/rate-limit deployment once domain is available.
- [ ] Optional Redis/rate-limit/cache evaluation.
- [ ] Evaluation and stress-test suites.

## Documentation split
- PRODUCTION_STATUS.md — evidence and live gates.
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
Verify → implement/fix → test → production verify → update evidence → main

## Definition of Done
- P0 production verification is green.
- Live LLM + Drive blockers are resolved.
- Migration/RLS verification is current.
- Storage and processing E2E are green.
- Monitoring/backup/rollback evidence exists.
- Frontend production smoke passes.
- Documentation reflects the verified state.
- CI remains green on main.

## Change Log
| Date | Change |
|---|---|
| 2026-10-06 | Reconciled tactical work with verified production evidence and separated product backlog from production blockers. |