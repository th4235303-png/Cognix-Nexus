> **Tactical tracking:** See `REMAINING_WORK.md` for Priority 0 (A→N).
> **Stack reference:** See `TOOLS.md`.
> **UI planning:** See `UI_PLAN.md`.

# Cognix Brain Vault — Execution Roadmap

This roadmap reconciles the original Phase 1–12 implementation history with Unified Master Plan v2.0.

## Current verified state

- Phases 1–12 foundation/hardening: delivered on `main`.
- Latest verified CI: run 36816101146, conclusion `success`.
- Netlify continuous deployment: intentionally paused by `netlify.toml`.
- Production database requirement: enabled in Render configuration.
- Full v2.0 Level Up 20: **not yet complete**; the earlier phase labels describe foundations, not all promised product behavior.

## Remaining implementation waves

### Phase 13 — AI Active Layer
Agent job/schedule/run/finding lifecycle, durable background execution, safe retries, TTL, evidence-bound findings, Synthesis Engine, Decision Support, Writing Assistant and Feynman Mode.

### Phase 14 — Learning Science
Decay prediction, interleaving, learning paths, explicit knowledge gaps and deep research mode.

### Phase 15 — Life Integration
Opt-in timeline, local-only mood state, user-triggered ambient learning, context restoration and encrypted time capsules.

### Phase 16 — Advanced Layer
Private wiki, growth/compounding metrics, evidence-backed idea generation, offline cache/local-model boundary and encrypted legacy handoff.

### Phase 17 — Cognix Core Integration
Source inbox expansion (URL/news/RSS), claim review, translation versioning, fact-check workflow, research reports and export integration.

### Phase 18 — Vizora Lens
Batch media, richer OCR/vision analysis, metadata, review state, media links and Drive package.

### Phase 19 — Native/Product UX
Offline-first reader/review, capture/share-sheet, camera OCR, voice capture, push, biometric vault boundary, JP/KR reading support, accessibility and responsive polish.

### Phase 20 — Production Engineering
Durable queue/leases, backup/restore verification, migration/schema checks, observability, evaluation datasets, E2E flows, stress tests, security tests and rollback drills.

### Phase 21 — Release
Only after all gates pass: re-enable Netlify deployment, deploy API/worker, configure domains/TLS/secrets, run smoke tests, verify health/readiness, then tag the release.

## Non-negotiable gates

1. No secret plaintext in server logs, prompts, embeddings or exports.
2. No AI output becomes canonical without the required human review.
3. Every generated answer has evidence/citation behavior appropriate to its source.
4. Durable production data never silently falls back to memory.
5. Jobs are idempotent and recoverable.
6. Optional providers fail closed.
7. Netlify stays paused during feature development.
8. Every implementation wave lands directly on `main` and must pass CI before being treated as complete.
