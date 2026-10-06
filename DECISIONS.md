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

## ADR-007 — Main-only execution
Cognix implementation and documentation changes are landed directly on main. The current operating rule is verify → implement/fix → test → production verify → update evidence → main.

## ADR-008 — Paid provider deferral
Paid LLM activation and Google Drive re-authorization are intentionally deferred. They are not current P0 blockers and must not be represented as completed or as reasons to stop UI/engineering work.

## ADR-009 — Free-tier Auth limitation
Supabase leaked-password protection is currently disabled because the active project is on the free tier and the feature is not available to enable there. The warning remains explicitly documented and is not treated as an application-code defect.