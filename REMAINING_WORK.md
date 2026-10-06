# Cognix Nexus — Remaining Work

> **Tactical tracking file.**
> See `ROADMAP.md` for strategic phases.
> See `TOOLS.md` for stack & services.
> See `UI_PLAN.md` for frontend planning.

---

## Current Status

| Layer | Status |
|---|---|
| Master Plan v3.0 | ✅ LOCKED |
| Foundation (Phase 1-12) | ✅ Delivered |
| Priority 0 (A→N) | ⏳ IN PROGRESS |
| Phase 13-21 | ❌ REMAINING |
| Documentation | ⚠️ PARTIAL |
| Production Ready | ❌ NOT YET |

**Correct Status:**
> Master Plan locked, Foundation largely built,
> Priority 0 verification/fixes remain,
> Phase 13-21 remain to be implemented progressively.

---

## Priority 0 — Pipeline Fix (A → N)

**Rule:** NO new features until all A→N pass.

### A. Production API Deploy Verify
- [ ] Render Dashboard → `cognix-nexus-api` → Live?
- [ ] Health check: `/api/v1/health` → 200 OK?
- [ ] Commit hash = latest `main`?

### B. Wikipedia Fix Production Verify
- [ ] Test: `https://en.wikipedia.org/wiki/Logistics`
- [ ] Status = Completed?
- [ ] Content extracted?
- [ ] 403 not triggered?

### C. Worker Queue Stuck/Failed Root Cause
- [ ] Query `processing_tasks` WHERE status IN ('queued','failed')
- [ ] Check worker logs (Render → `cognix-nexus-worker`)
- [ ] Identify: timeout? memory? logic?
- [ ] Fix root cause
- [ ] Verify stuck tasks resolved

### D. Book Processing E2E
- [ ] Upload 50-100p PDF (English + Myanmar + Scan)
- [ ] Book created (DB check)
- [ ] File stored (tier check)
- [ ] Processing queued
- [ ] Worker claims task
- [ ] Text extracted
- [ ] Chapters created
- [ ] Chunks created (**target: 100+**)
- [ ] Embeddings created (**target: 100+**)
- [ ] Status = completed

### E. Embedding Generation
- [ ] Embedding provider API key valid?
- [ ] Worker calls embedding API?
- [ ] Quota not exceeded?
- [ ] Vector dimension = 1536?
- [ ] pgvector extension enabled?
- [ ] Manual test: embed 1 chunk → verify in DB

### F. Search + RAG + Citation E2E
- [ ] Irrelevant question → "I don't know"
- [ ] Exact quote → source shown
- [ ] Semantic question → relevant chunks
- [ ] Multi-book question → both returned
- [ ] Contradictory sources → both shown
- [ ] `/brain/retrieval` endpoint works
- [ ] RRF score correct
- [ ] Citation format valid

### G. Source Inbox Error Matrix
| Case | Expected | Tested |
|---|---|---|
| Normal webpage | Success | [ ] |
| Wikipedia | Success | [ ] |
| Redirect | Follow | [ ] |
| Invalid URL | Clear error | [ ] |
| 403 | Fallback | [ ] |
| 429 | Backoff | [ ] |
| 5xx | Retry | [ ] |
| Timeout | Timeout error | [ ] |
| Non-HTML | Graceful | [ ] |
| Oversized | Size limit | [ ] |

### H. Storage Failure/Retry/Idempotency
- [ ] DB success + Storage failure → Recovery
- [ ] Storage success + DB failure → Recovery
- [ ] Worker crash mid-upload → Retry
- [ ] Duplicate upload → Idempotent
- [ ] Checksum mismatch → Error

### I. Vault E2E
- [ ] Create secret → encrypt locally
- [ ] Save ciphertext → server
- [ ] Logout → Login
- [ ] Fetch detail → decrypt locally
- [ ] Delete
- [ ] Verify no plaintext on server

### J. Google Drive Export E2E
- [ ] OAuth flow → signed state
- [ ] Callback → refresh token
- [ ] Export job → worker
- [ ] Drive upload → folder structure
- [ ] File verified in Drive
- [ ] Idempotency (no duplicate)

### K. RLS Ownership Audit (52 tables)
- [ ] Which tables are backend-only?
- [ ] Which tables frontend can access?
- [ ] Which rows belong to which user?
- [ ] Write RLS policies
- [ ] Unauthorized access test
- [ ] Document per-table decision

### L. Worker Cleanup + Naming
- [ ] Old `cognix-core-worker` → rename
- [ ] New `cognix-nexus-worker` (live worker NOT deleted)
- [ ] Update Render config
- [ ] Verify no downtime

### M. Full Regression Test
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] CI green on `main`

### N. Production Release Checklist
- [ ] All E2E verified
- [ ] Error handling complete
- [ ] Retry logic complete
- [ ] Idempotency complete
- [ ] Security audit complete
- [ ] Monitoring setup
- [ ] Backup verified
- [ ] Documentation updated

---

## Blockers (Immediate)

### 🔴 Blocker 1 — Paid LLM 402
- **Issue:** OpenRouter returns HTTP 402
- **Impact:** Production AI does not work with paid model
- **Fix:** Add credit OR free-tier fallback
- **Status:** [ ] Open

### 🔴 Blocker 2 — Netlify Paused
- **Issue:** `netlify.toml` pauses deployment
- **Impact:** Frontend not auto-deploying
- **Fix:** Re-enable after Priority 0
- **Status:** [ ] Open

### 🔴 Blocker 3 — SECURITY.md Template
- **Issue:** GitHub template, not real policy
- **Fix:** Write real security policy
- **Status:** [ ] Open

---

## Phase 13-21 — Remaining Waves

### Phase 13 — AI Active Layer
- [ ] Agent job/schedule/run/finding lifecycle
- [ ] Durable background execution
- [ ] Safe retries + TTL
- [ ] Evidence-bound findings
- [ ] Synthesis Engine (3+ sources)
- [ ] Decision Support (both sides)
- [ ] Writing Assistant (cite)
- [ ] Feynman Mode (90% mastery)

### Phase 14 — Learning Science
- [ ] Decay prediction
- [ ] Interleaving (2+ subjects)
- [ ] Learning paths (library-only)
- [ ] Knowledge gaps (explicit)
- [ ] Deep research mode

### Phase 15 — Life Integration
- [ ] Opt-in timeline
- [ ] Local-only mood
- [ ] User-triggered ambient
- [ ] Context restoration
- [ ] Encrypted time capsules

### Phase 16 — Advanced Layer
- [ ] Private wiki
- [ ] Growth/compounding metrics
- [ ] Evidence-backed ideas
- [ ] Offline cache/local model
- [ ] Encrypted legacy handoff

### Phase 17 — Cognix Core Integration
- [ ] Source inbox (URL/news/RSS)
- [ ] Claim review
- [ ] Translation versioning
- [ ] Fact-check workflow
- [ ] Research reports
- [ ] Export integration

### Phase 18 — Vizora Lens
- [ ] Batch media
- [ ] Richer OCR/vision
- [ ] Metadata
- [ ] Review state
- [ ] Media links
- [ ] Drive package

### Phase 19 — Native/Product UX
- [ ] Offline-first reader
- [ ] Capture/share-sheet
- [ ] Camera OCR
- [ ] Voice capture
- [ ] Push notifications
- [ ] Biometric vault
- [ ] JP/KR reading
- [ ] Accessibility
- [ ] Responsive polish

### Phase 20 — Production Engineering
- [ ] Durable queue/leases
- [ ] Backup/restore verification
- [ ] Migration/schema checks
- [ ] Observability
- [ ] Evaluation datasets
- [ ] E2E flows
- [ ] Stress tests
- [ ] Security tests
- [ ] Rollback drills

### Phase 21 — Release
- [ ] Re-enable Netlify
- [ ] Deploy API/worker
- [ ] Configure domains/TLS/secrets
- [ ] Run smoke tests
- [ ] Verify health/readiness
- [ ] Tag release

---

## Documentation Gaps

| File | Status | Priority |
|---|---|---|
| ARCHITECTURE.md | ❌ Missing | High |
| DATA_MODEL.md | ❌ Missing | High |
| PROMPTS.md | ❌ Missing | Medium |
| DECISIONS.md | ❌ Missing | Medium |
| TROUBLESHOOTING.md | ❌ Missing | Medium |
| CHANGELOG.md | ❌ Missing | Low |
| USER_GUIDE.md | ❌ Missing | Low |
| DEPLOYMENT.md | ⚠️ Partial | High |
| PIPELINE.md | ❌ Missing | High |
| AGENT.md | ❌ Missing | Medium |
| UI_PLAN.md | ❌ Missing | High |

---

## Non-Negotiable Gates

1. No secret plaintext in logs, prompts, embeddings, exports
2. No AI output becomes canonical without human review
3. Every answer has evidence/citation
4. Durable data never silently falls back to memory
5. Jobs are idempotent and recoverable
6. Optional providers fail closed
7. Netlify stays paused during feature dev
8. Every wave lands on `main` and passes CI

---

## AI Agent Instructions

**If you are an AI agent reading this file:**

1. **DO NOT add new features** until Priority 0 (A→N) all pass.
2. **Start with Priority 0** — work through A, B, C, ... N in order.
3. **Mark each item** `[x]` only after real verification.
4. **Do not trust existing labels** — verify in production.
5. **Work directly on `main`** — no long-lived branches.
6. **Pass CI before marking complete.**
7. **Reference Master Plan v3.0** for full feature specs.
8. **Follow Non-Negotiable Gates** (above).
9. **Report blockers** in Blockers section.
10. **Update this file** as work progresses.

**Priority Order:**
Priority 0 (A→N)
↓
Blockers
↓
Phase 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21
↓
Documentation
↓
Release

text

**Verification Cycle (per task):**
Implement → DB migration → API → Worker
→ Frontend → Test → Production verify
→ main commit → close

text

---

## Definition of Done

Cognix Nexus is production-ready when:

- [ ] Priority 0 (A→N) all pass
- [ ] Blockers resolved
- [ ] Phase 13-21 complete
- [ ] Documentation complete
- [ ] All Non-Negotiable Gates pass
- [ ] CI green on `main`
- [ ] Netlify re-enabled
- [ ] Production smoke tests pass
- [ ] Release tagged

---

## Change Log

| Date | Change |
|---|---|
| 2026-10-06 | Initial file created |
