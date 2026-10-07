# Cognix Nexus

Cognix Nexus is evolving into **Cognix Brain Vault**, a personal knowledge OS built on a research intelligence foundation.

## Product direction

Research sources → processing → evidence/claims → human review → approved knowledge → Brain Vault → notes/concepts/graph → retrieval/RAG → learning/synthesis.

Cognix Nexus remains the research and evidence foundation. Brain Vault is the primary knowledge layer built on top of it. Vizora Lens is a future media-intelligence layer that will feed images and other media into the same knowledge system.

## Current platform architecture

- Frontend: Next.js + React + TypeScript + Tailwind CSS
- Backend: FastAPI + Python processing worker
- Persistence: PostgreSQL / Supabase
- Authentication: Supabase Auth with backend JWT verification
- Delivery: Google Drive (provider activation currently deferred)
- Hosting: Netlify (frontend) + Render (API/worker)

## Storage architecture

| File type | Provider | Rule |
|---|---|---|
| Research images, covers, thumbnails | Cloudinary | <10 MB |
| Small PDFs, notes, summaries | Supabase Storage | <=50 MB, private |
| Large PDFs, EPUBs, research papers | Backblaze B2 | >50 MB |
| Export packages, backups | Google Drive | user-owned destination |

The book upload adapter routes <=50 MB to Supabase Storage and >50 MB to B2. Image ingestion is Cloudinary-only. Provider secrets remain backend-only.

## Research and Brain Vault foundation

The research lifecycle remains:

New → Queued → Extracting → Cleaning → Translating → Summarizing → Key Points → Fact-check Flagging → Trust Scoring → Needs Review → Approved → Drive Exported.

The Brain Vault foundation includes books, chapters/chunks, evidence-ranked search, notes, concepts, graph relationships, retrieval/RAG, language cards, evidence-bound synthesis, unified export and ciphertext-only Secret Vault storage.

Frontend core surfaces include books, reader, notes, graph and chat, with additional research, review, processing, Level Up, Vizora, vault and export surfaces.

## Book Intelligence

The Long-Book AI Reader is a background knowledge-production workflow:

**Library / Inbox → duplicate gate → AI Reading Room → partial/final distillation → Knowledge Vault → cross-book lessons / derived books.**

Current implementation includes:

- Phase 1–6: upload/import, category metadata, duplicate gate, extraction, background AI reading, chapter summaries, knowledge distillation and cross-book synthesis.
- Phase 7–12 foundation: durable review state, canonical/rejected knowledge, Markdown/structured export, lesson packs, derived books, provider-event audit, retry/backoff/checkpoints and Knowledge Vault UI.
- Supabase migrations 031/032 are applied in the live project.
- The worker can continue AI reading without the browser being open.
- Partial chapter knowledge and reading history are retained while processing continues.
- Source lineage is preserved for chapter/book summaries and cross-book outputs.

The workflow is designed so the user does **not** need to manually read the uploaded books first; AI processes them in the background and promotes useful material into the Knowledge Vault after the required review boundary.

## Current implementation / release state

**Code-side tactical backlog:** no known blocking implementation item remains in REMAINING_WORK.md at this checkpoint. The remaining release work is primarily real-infrastructure verification and operator/device gates.

Pending external verification:

- Real AI provider E2E with production-safe credentials.
- Google Drive OAuth/account authorization and real export verification.
- Supabase Storage and Backblaze B2 live drills.
- Authenticated Playwright production smoke.
- Mobile EAS/device smoke.
- Full keyboard/screen-reader/responsive accessibility sweep.
- Lighthouse/performance run.
- Production backup → restore → rollback drill.
- Final production smoke and release approval.
- GDPR export/delete remains an open product/compliance gate.
- Sentry live ingestion remains to be verified.

These are intentionally **not** marked PASS from static code inspection. See PRODUCTION_E2E_STATUS.md for the gate-by-gate evidence matrix.

## Production verification state

- Render API/worker and current main-line services are tracked in PRODUCTION_STATUS.md.
- Cloudinary live upload/read/checksum/delete has been verified.
- Supabase Storage and B2 full provider drills remain pending.
- Paid LLM activation is intentionally deferred and is not a current P0 blocker.
- Google Drive OAuth/provider verification requires the account-owner authorization step.
- Supabase Auth still reports leaked-password protection disabled. The active project is on the free tier, so this remains an account-plan limitation rather than an application-code defect.
- Netlify production is older than current main at the current checkpoint; final deployment remains gated on release approval.

See PRODUCTION_STATUS.md for evidence and REMAINING_WORK.md for the tactical release backlog.

## Documentation map

- PRODUCTION_STATUS.md — live evidence and release gates
- PRODUCTION_E2E_STATUS.md — external verification matrix
- REMAINING_WORK.md — tactical execution backlog
- ROADMAP.md — strategic product waves
- TOOLS.md — service catalog
- ARCHITECTURE.md — system boundaries
- DATA_MODEL.md — ownership and lineage
- DEPLOYMENT.md — release/runbook
- PIPELINE.md — processing and retrieval lifecycle
- AGENT.md — agent contract
- SECURITY.md — security policy
- TROUBLESHOOTING.md — operational recovery
- DECISIONS.md — durable architecture decisions
- UI_PLAN.md — UI product/design requirements
- UI_STATUS.md — UI implementation and verification checklist

All implementation and documentation changes land on main.

## Reference corpus

The current book workflow supports **9 categories / 170 files**:

- Business, Entrepreneurship & Finance
- Communication & Negotiation
- Creativity & Tech
- Future Tech
- Leadership & Management
- Productivity, Habits & Discipline
- Psychology & Critical Thinking
- Self-Help & Emotional Intelligence
- Stoicism & Philosophy

See web-platform/docs/book-intelligence-product-spec.md for the locked Book Intelligence contract.

## Strategic roadmap

The longer-term product waves remain in ROADMAP.md and web-platform/docs/master-plan-v2.md. These include the AI Active Layer, Learning Science, Life Integration, Advanced Layer, Cognix Core research integration, Vizora Lens, native polish and production engineering.

Strategic roadmap items are **not treated as current P0 blockers** unless they are moved into REMAINING_WORK.md as a concrete implementation task.
