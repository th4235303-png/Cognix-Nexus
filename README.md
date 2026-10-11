# Cognix Nexus

Cognix Nexus is evolving into **Cognix Brain Vault**, a personal knowledge OS built on a research intelligence foundation.

## What it is

Research sources → processing → evidence/claims → human review → approved knowledge → Brain Vault → notes/concepts/graph → retrieval/RAG → learning/synthesis.

Cognix Core is the research/evidence foundation. Brain Vault is the durable personal knowledge layer. Vizora Lens is the future media-intelligence boundary.

## Stack

- Frontend: Next.js + React + TypeScript + Tailwind CSS.
- Backend: FastAPI + Python worker.
- Persistence/Auth: PostgreSQL/Supabase + Supabase Auth.
- Retrieval: pgvector plus lexical/semantic ranking and RRF.
- Storage: Cloudinary media, Supabase Storage for small private artifacts, Backblaze B2 for large originals, Google Drive for user-owned exports/backups.
- Hosting: Netlify frontend + Render API/worker.

## Current snapshot

The implementation is at release-candidate / pre-final-production-verification state. CI and CodeQL passed on main commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae`; the API and worker deployments for that commit were observed live on 2026-10-11. The repository and live Supabase migration heads were both verified at 032 on 2026-10-08, and must be rechecked before release. External provider, OAuth, browser/device, accessibility/performance, recovery and compliance gates remain pending. Live Render settings also need reconciliation against `render.yaml`, and live environment-variable cleanup has not yet been verified. Final production smoke and release remain blocked.

AI provider endpoints and model IDs are maintained in backend code; Render should store provider credentials and required service/integration configuration, not model/URL overrides. Production embeddings remain fixed at 1536 dimensions, so Cohere is currently the compatible production embedding route. See CURRENT_STATE.md for status/evidence, ROADMAP.md for strategic scope, and PROJECT_OVERVIEW.md for architecture/product boundaries.

## Documentation map

- PROJECT_OVERVIEW.md — product and architecture overview
- CURRENT_STATE.md — current status, evidence, gates and next actions
- ROADMAP.md — canonical strategic roadmap
- UI_DESIGN_SYSTEM.md — UI rules and design system
- TOOL.md — engineering/documentation workflow
- SECURITY.md — security policy
- docs/ARCHITECTURE.md — detailed architecture and ADR history
- docs/DATA_MODEL.md — schema, ownership, RLS and migration discipline
- docs/PIPELINE.md — processing pipeline and lifecycle boundaries
- docs/PROMPTS.md — AI prompt governance and evaluation rules
- docs/DEVELOPMENT.md — development setup/checks
- docs/TESTING.md — testing and acceptance
- docs/DEPLOYMENT.md — deployment/release operations
- docs/OPERATIONS.md — runtime operations/recovery
- docs/DATABASE.md — schema, RLS and migration discipline
- docs/API.md — API contract reference
- docs/AI_RAG.md — processing, AI and retrieval
- docs/STORAGE.md — storage provider roles
- docs/TROUBLESHOOTING.md — operational troubleshooting
- docs/CHANGELOG.md — release history
- docs/USER_GUIDE.md — end-user workflow and roadmap boundaries
- docs/AGENT.md — AI agent behavior and activation guard
- docs/EVALUATION_DATASETS.md — deterministic evaluation corpus plan
- docs/features/ — feature-specific behavior
- docs/runbooks/ — operational procedures
- archive/legacy/ — historical source documents retained for traceability

All implementation and documentation changes land on main.
