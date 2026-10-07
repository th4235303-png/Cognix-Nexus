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

## ADR-010 — Background AI reading

Book processing is a durable server-side knowledge-production job. The user may upload a book and leave; the browser is not required for continued reading/extraction.

## ADR-011 — Exact duplicate uploads stop automatically

An exact content fingerprint match must not start another expensive reading run. Possible same-book matches remain reviewable; explicit reprocessing creates a new version.

## ADR-012 — Partial knowledge is visible but not final

Completed chapters may expose summaries and keys before the book finishes. Partial artifacts carry status, timestamps, version and source lineage and cannot masquerade as final synthesis.

## ADR-013 — Derived knowledge is separate from originals

Original books remain traceable/archived. Distilled knowledge, lesson packs and derived books are separate records with source manifests.

## ADR-014 — Cross-book synthesis preserves lineage

Category lessons and derived books must retain contributing source/version references and expose disagreement rather than flattening contradictions.

## ADR-015 — Progress is an auditable timeline

Progress is based on durable completed units/checkpoints, not a client-side timer. Users can inspect the timeline while a book is incomplete.
