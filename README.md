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

The implementation is at release-candidate / pre-final-production-verification state. Repository and live Supabase migration heads are both 032, and the previously identified four VERIFY items are closed with evidence. External provider, OAuth, browser/device, accessibility/performance, recovery and compliance gates remain pending, so final production smoke and release are still blocked.

See CURRENT_STATE.md for status and evidence, ROADMAP.md for strategic scope, and PROJECT_OVERVIEW.md for architecture/product boundaries.

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
