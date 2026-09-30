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

## Future phases

1. PDF/EPUB ingestion adapters and page-accurate source spans
2. semantic embeddings + pgvector
3. L1–L7 hierarchical book intelligence
4. cross-book synthesis and contradiction review
5. language tutor + FSRS
6. document assistant + OCR
7. client-side encrypted Secret Vault
8. unified export
9. Expo mobile client
10. Vizora Lens media intelligence

## Architecture rules

- Research evidence and personal knowledge remain linked but distinct domains.
- AI-generated content is never automatically canonical.
- Human review remains the approval boundary for evidence-derived knowledge.
- Secrets remain isolated from ordinary knowledge records.
- Media/Vizora is a future input layer, not a replacement for Brain Vault.
- Original binary storage must sit behind a storage abstraction; the current book foundation persists extracted text in PostgreSQL.
