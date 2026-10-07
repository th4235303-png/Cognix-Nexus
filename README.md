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

## Production verification state

- Render API and worker are live on the latest verified main revision at the current checkpoint.
- Production migration ledger includes migration 028, which removes redundant level-up deny policies.
- Cloudinary live upload/read/checksum/delete has been verified.
- Supabase Storage and B2 full provider drills remain pending.
- Paid LLM activation is intentionally deferred and is not a current P0 blocker.
- Google Drive OAuth/provider verification is intentionally deferred.
- Supabase Auth still reports leaked-password protection disabled. The active project is on the free tier, so this remains an account-plan limitation rather than an application-code defect.
- UI completion/polish is the active release track.

See PRODUCTION_STATUS.md for evidence, REMAINING_WORK.md for actions, UI_PLAN.md for UI requirements, and UI_STATUS.md for UI implementation status.

## Documentation map

- PRODUCTION_STATUS.md — live evidence and release gates
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

## Book Intelligence mode

The book workflow is designed as background AI reading, not manual reading as a prerequisite. The current reference corpus is **9 categories / 170 files**:

- Business, Entrepreneurship & Finance
- Communication & Negotiation
- Creativity & Tech
- Future Tech
- Leadership & Management
- Productivity, Habits & Discipline
- Psychology & Critical Thinking
- Self-Help & Emotional Intelligence
- Stoicism & Philosophy

The lifecycle is separated into **Library / Inbox → AI Reading Room → Knowledge Vault / Completed**. Exact duplicate uploads stop before expensive processing; incomplete runs resume from checkpoints; partial chapter knowledge is visible before the book finishes; and stable knowledge can later be synthesized into category lesson packs, study guides and derived books with source lineage.

See web-platform/docs/book-intelligence-product-spec.md for the locked product contract.
