# Cognix Brain Vault

Brain Vault is the personal knowledge layer built on top of Cognix Core. Cognix Core remains the research/evidence foundation; Brain Vault adds durable books, notes, concepts, retrieval, and later learning, documents, and secure storage.

## Current implementation

The first implementation is intentionally evidence-first and storage-neutral.

### Book foundation

- `books`
- `chapters`
- `chunks`
- ordered reader data
- content hashing
- text import
- per-book evidence search

### Second brain

- `notes`
- `note_sources`
- `concepts`
- `concept_links`
- note backlinks
- activity events for knowledge changes

### Retrieval

The first retrieval layer uses PostgreSQL full-text indexes and deterministic evidence ranking. It does not claim to be semantic RAG yet.

The next retrieval milestone is:

```text
chunk → embedding → pgvector → evidence selection → model synthesis → citation
```

AI answers must preserve source/chunk references.

## API

Brain Vault endpoints live under `/brain`:

- `GET /brain/books`
- `POST /brain/books`
- `GET /brain/books/{book_id}`
- `GET /brain/books/{book_id}/chapters`
- `GET /brain/books/{book_id}/chapters/{chapter_id}`
- `GET /brain/books/{book_id}/search?q=...`
- `GET /brain/notes`
- `POST /brain/notes`
- `GET /brain/notes/{note_id}/backlinks`
- `GET /brain/concepts`
- `POST /brain/concepts`
- `POST /brain/concept-links`
- `GET /brain/graph`
- `GET /brain/query?q=...`

## Frontend

Current Brain Vault routes:

- `/books`
- `/books/[id]`
- `/notes`
- `/graph`
- `/chat`

These are real API-backed surfaces, not mock/demo data.

## Migration order

Brain Vault schema is introduced after the existing Cognix migrations:

1. `001_initial.sql`
2. `002_api_contract_alignment.sql`
3. `003_persistence_hardening.sql`
4. `004_brain_vault_foundation.sql`
5. `005_brain_vault_search.sql`

The migrations are applied automatically by the existing database bootstrap.

## Delivery phases 1–13

1. **PDF/EPUB ingestion** — local extraction, ordered sections, page metadata, content hashing, and storage abstraction.
2. **Semantic retrieval** — provider-neutral embeddings, pgvector indexing, and cited vector search when configured.
3. **Hierarchical intelligence** — versioned L1–L7 summaries with chunk-level source links.
4. **Cross-book synthesis** — evidence-only synthesis records, generated citations, and reviewable contradiction candidates.
5. **Language Tutor** — language cards with spaced-review scheduling, ratings, lapses, and review history.
6. **Document Assistant** — bounded OCR ingestion, per-page OCR results, persisted job state, and failure reporting.
7. **Secret Vault** — ciphertext, nonce, KDF salt, and KDF parameters only; decryption material stays client-side.
8. **Unified export** — Brain Vault export extends the existing research export contract rather than replacing it.
9. **Mobile foundation** — Expo client foundation is present for the same Brain Vault API surface.
10. **Vizora Lens** — image ingest, hashing, OCR, and media asset metadata form the input boundary for future visual intelligence.
11. **Production hardening** — request IDs, security headers, configurable authentication, rate limiting, readiness checks, bounded uploads, and regression CI.
12. **Operational readiness** — explicit production database readiness, bounded runtime rate limiting, environment guidance, and release/rollback operations.
13. **AI Active Layer foundation** — durable agent jobs, runs, findings and worker execution; evidence-bound model output remains `needs_review` and never becomes canonical automatically.

### Verification contract

Every phase is expected to preserve these invariants:

- source evidence remains traceable to its original source/chunk;
- AI-generated text remains non-canonical until the existing human-review boundary is satisfied;
- secret records contain ciphertext metadata only;
- optional providers fail closed when they are not configured;
- upload endpoints enforce file-type and size limits;
- /health remains a liveness check while /ready reports persistence readiness;
- the frontend and backend verification commands remain part of CI.
