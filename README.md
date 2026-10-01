# Cognix Core

Cognix Core is evolving into **Cognix Brain Vault**, a personal knowledge OS built on a research intelligence foundation.

## Product direction

```text
Research sources
  → processing
  → evidence / claims
  → human review
  → approved knowledge
  → Brain Vault
  → notes / concepts / graph
  → retrieval / RAG
  → learning / synthesis
```

Cognix Core remains the research and evidence foundation. Brain Vault is the primary knowledge layer built on top of it. Vizora Lens is a future media-intelligence layer that will feed images and other media into the same knowledge system.

## Current platform architecture

- Frontend: Next.js + React + TypeScript + Tailwind CSS
- Backend: FastAPI + Python processing worker
- Persistence: PostgreSQL / Supabase
- Authentication: Supabase Auth with backend JWT verification
- Delivery: Google Drive
- Hosting: Netlify (frontend) + Render (API/worker)

## Repository structure

```text
web-platform/
├── frontend/   Next.js application
├── backend/    FastAPI API, worker, migrations, tests
└── docs/       architecture, deployment, operations, Brain Vault

.github/        CI and dependency automation
README.md       project overview
SECURITY.md     security policy
render.yaml     Render services
netlify.toml    Netlify configuration
```

## Research foundation

The existing research lifecycle remains:

```text
New
→ Queued
→ Extracting
→ Cleaning
→ Translating
→ Summarizing
→ Key Points
→ Fact-check Flagging
→ Trust Scoring
→ Needs Review
→ Approved
→ Drive Exported
```

Human-edited Myanmar translation and critical fact-check warnings remain separate from AI-derived content. Approval still blocks unresolved critical warnings and missing approved Myanmar translation.

## Brain Vault foundation

The first Brain Vault layer is now API-backed and durable:

- Book Library
- Book reader data model
- Chapters and chunks
- Evidence-ranked book search
- Second Brain notes
- Note-to-source relationships
- Note backlinks
- Concepts
- Concept relationships
- Knowledge graph API
- Evidence-first Brain Query

Backend routes are under `/brain`.

Frontend routes are:

- `/books`
- `/books/[id]`
- `/notes`
- `/graph`
- `/chat`

The retrieval layer supports deterministic PostgreSQL search and an optional pgvector semantic path with source/chunk citations. Semantic embeddings are provider-neutral and enabled only when embedding configuration is supplied.

See `web-platform/docs/brain-vault.md` for the detailed architecture and phase roadmap.

## Brain Vault migration order

1. `001_initial.sql`
2. `002_api_contract_alignment.sql`
3. `003_persistence_hardening.sql`
4. `004_brain_vault_foundation.sql`
5. `005_brain_vault_search.sql`
6. `006_brain_vault_advanced.sql`
7. `007_book_storage.sql`

The existing database bootstrap applies the Brain Vault migrations after the Cognix Core schema.

## Implemented Brain Vault capabilities

- PDF/EPUB upload and extraction
- Original binary storage behind a persistent storage adapter
- Page/section metadata on extracted chunks
- Optional pgvector embedding index and semantic retrieval
- Versioned L1–L7 summary records with source linkage
- Language cards with spaced-review scheduling
- Evidence-only synthesis records
- Unified Brain Vault JSON export
- Contradiction candidate review surface (human confirmation required)
- Ciphertext-only Secret Vault storage boundary

## Product phases 1–11

The Brain Vault roadmap is implemented as a continuous delivery sequence. The repository keeps the phase boundaries explicit so each layer can be regression-tested without replacing the existing research foundation.

1. PDF/EPUB ingestion and page-accurate source spans — implemented
2. Semantic embeddings + pgvector — implemented, provider-configured
3. L1–L7 hierarchical book intelligence — implemented with cited synthesis boundaries
4. Cross-book synthesis + contradiction review — implemented with human-review state
5. Language Tutor + FSRS-style scheduling — implemented
6. Document Assistant + OCR — implemented with bounded uploads and job persistence
7. Client-side encrypted Secret Vault — implemented as ciphertext-only server storage
8. Unified export and automation surfaces — implemented without replacing the existing Drive export contract
9. Expo mobile foundation — implemented
10. Vizora Lens media intelligence input boundary — implemented for image ingest + OCR, with richer vision provider integration remaining configuration-dependent
11. Production hardening and verification — implemented with request IDs, security headers, optional auth enforcement, rate limiting, readiness checks, and CI regression coverage

Phase 11 is intentionally an engineering hardening phase: it does not make AI output canonical and does not bypass the existing human-review boundaries.

## Google Drive output

```text
/cognix-core/YYYY-MM-DD/research-id/
├── source.json
├── original-reference.txt
├── summary.md
├── myanmar-summary.md
├── claims.json
└── review.json
```

Brain Vault exports will extend this contract rather than replacing the existing research export.

## Local development

Frontend:

    cd web-platform/frontend
    npm ci
    npm run dev

Backend:

    cd web-platform/backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

## Verification

    cd web-platform/frontend
    npm run typecheck
    npm run lint
    npm run build

    cd ../backend
    python -m compileall app
    python -m unittest discover -s tests -v

Never commit API keys, OAuth refresh tokens, database passwords, or other provider secrets.

No Logixa Flow webhook is used.
