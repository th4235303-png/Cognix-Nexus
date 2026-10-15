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

**Release status: blocked / pre-final-production-verification.** The repository's latest main commit is `f58a9fc3c9bb59ce0791b7b117bfa4ae8ebe446f` (2026-10-14). Phase 13–21 runtime code exists in the repository, but production activation remains behind the release gate.

A fresh infrastructure audit on **2026-10-15** found:

- Supabase `Cognix-Core` is `ACTIVE_HEALTHY`; live migration head is `033_rls_policy_initplan_indexes`.
- Supabase security advisor still reports leaked-password protection disabled. Performance advisor reports INFO-level unused-index findings; no new critical performance finding was identified.
- Render has three live services: `Cognix-Core` API, `cognix-core-worker-runtime`, and `cognix-nexus-frontend`. The worker is live on commit `5067c12b`; the latest API deploy for the same commit failed after a successful build, so the API must be reconciled before release.
- Render frontend is currently the actual live frontend target; repository docs previously naming Netlify are stale and have been corrected in this documentation pass.
- Cloudflare has one connected account but currently exposes no zones, Workers scripts, or Pages projects. R2 is not enabled, so Cloudflare is not a production storage/runtime dependency today.
- The repository contains no `vercel.json` and no Vercel reference was found by repository search. There is therefore no evidence that Vercel is the current deployment platform.
- Google Drive/export, authenticated browser smoke, recovery/restore, GDPR, Sentry, accessibility, performance, mobile/device and final production smoke still require fresh evidence before release approval.

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
