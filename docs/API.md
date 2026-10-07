# Cognix Nexus — API

> Owner: API contracts
> Update when: route contracts, authentication boundaries, or provider-facing API behavior changes
> Last Updated: 2026-10-08
> Do NOT put here: live production evidence.

## Authentication

Backend JWT verification is required in production. User-owned API access is owner-scoped.

## Brain Vault routes

The Brain Vault API includes routes for:

- books list/create/detail;
- chapters and ordered reader data;
- book search;
- notes;
- note backlinks;
- concepts;
- concept links;
- graph;
- query/retrieval.

The historical Brain Vault source lists these under `/brain`:

`GET /brain/books`, `POST /brain/books`, `GET /brain/books/{book_id}`, `GET /brain/books/{book_id}/chapters`, `GET /brain/books/{book_id}/chapters/{chapter_id}`, `GET /brain/books/{book_id}/search?q=...`, `GET /brain/notes`, `POST /brain/notes`, `GET /brain/notes/{note_id}/backlinks`, `GET /brain/concepts`, `POST /brain/concepts`, `POST /brain/concept-links`, `GET /brain/graph`, `GET /brain/query?q=...`.

These route names are preserved from the source documentation; implementation should be checked before treating the list as an exhaustive current API inventory.

## Health

- `/health` — liveness.
- `/ready` — persistence readiness.

## Provider boundaries

Provider configuration and secrets remain backend-only. Missing/invalid provider credentials must produce explicit failure rather than an unverified success state.
