# Cognix Nexus — Architecture Decisions

## ADR-001 — Tiered storage
Cloudinary handles research media; private Supabase Storage handles small artifacts; B2 handles large originals; Google Drive handles user-owned exports/backups.

## ADR-002 — Evidence-first AI
AI output is never canonical by default. Evidence and review state remain durable.

## ADR-003 — Owner isolation
User data is isolated through owner_id and owner-scoped RLS/persistence context. Legacy ownerless records fail closed.

## ADR-004 — Durable worker leases
Real book/export rows carry leases and fencing tokens. Synthetic task IDs are not accepted as the source of truth for those workflows.

## ADR-005 — SSRF defense in depth
Outbound fetching validates URL scheme, destination and redirects, then uses pinned validated transport.

## ADR-006 — Documentation separation
Tracking, production evidence, architecture, pipeline, data, deployment, security and UI planning are separate documents so a stale checklist cannot masquerade as live evidence.