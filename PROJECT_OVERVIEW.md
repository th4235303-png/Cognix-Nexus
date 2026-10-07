# Cognix Nexus — Project Overview

> Owner: Project documentation
> Update when: product or architecture boundaries materially change
> Last Updated: 2026-10-08
> Do NOT put here: release checklists, live verification evidence, tactical backlog, detailed domain runbooks, or UI implementation checklists.

## What this is

Cognix Nexus is evolving into **Cognix Brain Vault**, a personal knowledge OS built on a research intelligence foundation.

Cognix Core remains the research/evidence foundation. Brain Vault is the durable personal knowledge layer. Vizora Lens is the future media-intelligence boundary.

## Product flow

Research sources → processing → evidence/claims → human review → approved knowledge → Brain Vault → notes/concepts/graph → retrieval/RAG → learning/synthesis.

For long books, the product flow is:

Library / Inbox → duplicate gate → AI Reading Room → partial/final distillation → Knowledge Vault → cross-book lessons / derived books.

## System architecture

- Frontend: Next.js + React + TypeScript + Tailwind CSS.
- API: FastAPI.
- Worker: dedicated Python processing worker.
- Persistence/Auth: PostgreSQL / Supabase, with Supabase Auth and backend JWT verification.
- Vector retrieval: PostgreSQL/pgvector.
- Media: Cloudinary.
- Small private artifacts: Supabase Storage.
- Large originals: Backblaze B2.
- User-owned exports/backups: Google Drive.
- Frontend hosting: Netlify.
- API/worker hosting: Render.

The current storage target is tiered: Supabase Storage for artifacts up to 50 MB and B2 above 50 MB; Cloudinary remains the media provider. R2 has an adapter but is not the configured tiered target and is treated as optional until live role verification.

## Trust boundaries

1. Browser — user session, UI state and client-side vault encryption boundary.
2. API — authentication, authorization, persistence and provider orchestration.
3. Worker — durable jobs, leases, extraction, embeddings and exports.
4. Database — canonical durable records, owner isolation and evidence lineage.
5. External providers — optional execution boundaries that fail closed.

## Core invariants

- AI output is derived evidence, not canonical truth.
- Required human review gates remain durable.
- User-owned records are owner-scoped.
- Durable jobs are resumable and idempotent.
- Provider failures are explicit; durable state does not silently fall back to memory.
- Source/chunk lineage is preserved for retrieval and synthesis.
- Secrets remain backend-only.

## Runtime documentation

Detailed architecture, data, API, pipeline, deployment, operations, storage, AI/RAG, testing and troubleshooting live under docs/.

Release status belongs in CURRENT_STATE.md; strategic scope belongs in ROADMAP.md; working protocol belongs in TOOL.md; security policy belongs in SECURITY.md.
