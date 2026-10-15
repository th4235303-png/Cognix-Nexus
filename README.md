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
- Current hosting: Render frontend + Render API/worker.
- Netlify: legacy/documented frontend target; no active Netlify service is confirmed by the current connected account audit.
- Vercel: no Vercel configuration or active Vercel deployment was found in the repository/account integrations available to this audit.
- Cloudflare: account is connected, but no active zone, Workers script, or Pages project is currently visible; R2 is not enabled.

## Current snapshot

**Release status: BLOCKED pending final production verification.** The P0 code/CI/deployment blockers are resolved on main revision `54be85aa883b589b392d14279ea73e830951a522` (2026-10-15): Cognix Core CI and CodeQL pass; Render frontend, API and worker are live; migrations 034–041 are recorded as applied; API logs show `/health 200 OK`; and worker logs confirm PostgreSQL-backed startup.

The remaining release gates are current post-deploy `/ready` evidence, safe live environment-name reconciliation, authenticated production browser smoke, real provider and Google Drive export/retry/idempotency acceptance, controlled Book Intelligence corpus acceptance, accessibility/performance/mobile/Sentry/GDPR/recovery evidence, and final production smoke. Supabase Auth leaked-password protection remains a security WARN pending an explicit decision. Phase 13–21 production activation and release tagging remain blocked until required gates pass.

See `CURRENT_STATE.md` for evidence-backed status and next actions, `ROADMAP.md` for strategic scope, and `PROJECT_OVERVIEW.md` for architecture/product boundaries.

## Documentation map

- `PROJECT_OVERVIEW.md` — product and architecture overview
- `CURRENT_STATE.md` — current status, evidence, gates and next actions
- `ROADMAP.md` — canonical strategic roadmap
- `UI_DESIGN_SYSTEM.md` — UI rules and design system
- `TOOL.md` — engineering/documentation workflow
- `SECURITY.md` — security policy
- `docs/ARCHITECTURE.md` — detailed architecture and ADR history
- `docs/DATA_MODEL.md` — schema, ownership, RLS and migration discipline
- `docs/PIPELINE.md` — processing pipeline and lifecycle boundaries
- `docs/PROMPTS.md` — AI prompt governance and evaluation rules
- `docs/DEVELOPMENT.md` — development setup/checks
- `docs/TESTING.md` — testing and acceptance
- `docs/DEPLOYMENT.md` — deployment/release operations
- `docs/OPERATIONS.md` — runtime operations/recovery
- `docs/DATABASE.md` — schema, RLS and migration discipline
- `docs/API.md` — API contract reference
- `docs/AI_RAG.md` — processing, AI and retrieval
- `docs/STORAGE.md` — storage provider roles
- `docs/TROUBLESHOOTING.md` — operational troubleshooting
- `docs/CHANGELOG.md` — release history
- `docs/USER_GUIDE.md` — end-user workflow and roadmap boundaries
- `docs/AGENT.md` — AI agent behavior and activation guard
- `docs/EVALUATION_DATASETS.md` — deterministic evaluation corpus plan
- `docs/features/` — feature-specific behavior
- `docs/runbooks/` — operational procedures
- `archive/legacy/` — historical source documents retained for traceability

All implementation and documentation changes land on `main`.
