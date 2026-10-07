# Cognix Nexus — Architecture

> Owner: Architecture
> Update when: system boundaries, major components, invariants, or durable architectural decisions change
> Last Updated: 2026-10-08
> Do NOT put here: live release checklist or tactical backlog.

## Product boundary
Cognix Core is the research/evidence foundation. Brain Vault is the durable personal knowledge layer. Vizora Lens is the media-intelligence boundary.

## Runtime
- Next.js/React/TypeScript frontend.
- FastAPI backend.
- Dedicated Python worker.
- Supabase PostgreSQL + pgvector + Auth.
- Cloudinary for research media.
- Supabase Storage for small private artifacts.
- Backblaze B2 for large originals.
- Google Drive for user-owned exports/backups.
- Render for API/worker; Netlify for frontend.

## Trust boundaries
1. Browser: user session, client-side vault encryption, UI state.
2. API: authentication, authorization, persistence, provider orchestration.
3. Worker: durable jobs, leases, extraction, embeddings, export.
4. Database: canonical durable records, owner isolation, evidence lineage.
5. Providers: optional external execution; failures must fail closed.

## Core invariants
AI output is derived evidence, not canonical truth. Required human review gates remain durable. Durable state must not silently fall back to memory. Jobs are resumable/idempotent. Owner isolation is enforced. Evidence/source lineage is retained.

## Data flow
Source/book → durable storage → extraction → chunks → embeddings/search → evidence selection → optional model synthesis → citations → review/approved knowledge → Brain Vault.

## Retrieval
Current retrieval is hybrid lexical/semantic retrieval with RRF/ranking and source/chunk citations. Older vector-only/non-semantic claims are historical and are not current source of truth.

## Storage routing
- Research images/covers/thumbnails: Cloudinary.
- Small PDFs/notes/summaries: private Supabase Storage, up to 50 MB tier.
- Large PDFs/EPUBs/papers: B2, above 50 MB tier.
- Exports/backups: Google Drive.
- R2 adapter exists but its production role is VERIFY/optional, not the configured tiered target.

## Durable decisions
### ADR-001 — Tiered storage
Cloudinary for research media; Supabase Storage for small artifacts; B2 for large originals; Drive for user-owned exports/backups.
### ADR-002 — Evidence-first AI
AI output remains non-canonical until the required review boundary.
### ADR-003 — Owner isolation
Owner-scoped persistence and RLS; legacy ownerless access fails closed.
### ADR-004 — Durable worker leases
Real book/export rows use leases and fencing tokens.
### ADR-005 — SSRF defense in depth
Validate URL scheme/destination and every redirect, then use validated transport.
### ADR-006 — Documentation separation
Status, architecture, pipeline, data, deployment, security and UI planning have separate canonical owners.
### ADR-007 — Main-only execution
Implementation/documentation changes land on main using verify → implement/fix → test → production verify → update evidence → main.
### ADR-008 — Paid provider deferral
Paid LLM activation and Drive re-authorization are deferred and are not current P0 blockers.
### ADR-009 — Free-tier Auth limitation
Leaked-password protection remains disabled due to the current free-tier account limitation; this is not an application-code defect.
### ADR-010 — Background AI reading
Book processing continues server-side without the browser remaining open.
### ADR-011 — Exact duplicate stop
Exact content fingerprints stop duplicate expensive processing; possible matches require review.
### ADR-012 — Partial knowledge not final
Partial chapter artifacts remain visibly partial/draft and cannot masquerade as final synthesis.
### ADR-013 — Derived knowledge separate
Original books remain separate from distilled knowledge and derived books.
### ADR-014 — Cross-book lineage
Cross-book synthesis preserves contributing source/version references and disagreement.
### ADR-015 — Auditable progress timeline
Progress derives from durable completed units/checkpoints, not a client timer.

## Historical implementation corrections
- Export worker state transition moved into the export service.
- Vault list stopped returning ciphertext.
- Retrieval moved from vector-only to hybrid RRF.
