# Cognix Nexus — Architecture

## Product boundary
Cognix Core is the research/evidence foundation. Brain Vault is the durable personal knowledge layer. Vizora Lens is the media-intelligence boundary.

## Runtime
- Next.js/React/TypeScript frontend.
- FastAPI backend.
- Dedicated Python worker.
- Supabase PostgreSQL + pgvector + Auth.
- Cloudinary for small research media.
- Supabase Storage for private small artifacts.
- Backblaze B2 for large originals.
- Google Drive for user-owned exports/backups.

## Trust boundaries
1. Browser: user session, client-side vault encryption, UI state.
2. API: authentication, authorization, persistence, provider orchestration.
3. Worker: durable jobs, leases, extraction, embeddings, export.
4. Database: canonical durable records, owner isolation, evidence lineage.
5. Providers: optional external execution; failures must fail closed.

## Core invariant
AI output is derived evidence, not canonical truth. Human review is required where the product contract says approval is needed.

## Data flow
Source/book → durable storage → extraction → chunks → embeddings/search → evidence selection → optional model synthesis → citations → review/approved knowledge → Brain Vault.

## Storage routing
- Research images/covers/thumbnails: Cloudinary, under the configured media limit.
- Small PDFs/notes/summaries: private Supabase Storage, up to 50 MB tier.
- Large PDFs/EPUBs/papers: B2, above 50 MB tier.
- Exports/backups: Google Drive.

## Documentation boundaries
See DATA_MODEL.md for ownership/lineage, PIPELINE.md for processing, DEPLOYMENT.md for release operations, and SECURITY.md for security policy.