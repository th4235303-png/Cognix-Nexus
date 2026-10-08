# Cognix Nexus — Data Model

> Owner: Data/architecture
> Update when: schema, ownership, RLS, lifecycle or migration discipline changes
> Last Updated: 2026-10-08

## Canonical persistence
PostgreSQL/Supabase is the canonical durable store. Runtime state must not silently fall back to client memory.

## Core domains
- Sources/books/chapters/chunks: ingestion and evidence-bearing content.
- Reading/progress/events: durable user activity and checkpoints.
- Knowledge/lesson packs/derived books: reviewed or derived knowledge with provenance.
- Agent jobs/runs/findings: evidence-bound active-layer state; findings remain review-gated.
- Future contracts: learning, life integration, advanced artifacts, media boundaries and release evidence are prepared without autonomous activation.

## Ownership and RLS
Every durable user-owned record must carry owner context or an equivalent enforceable relationship. Cross-owner access fails closed. Service-role operations must explicitly preserve owner scope.

## Evidence lineage
Derived findings, summaries, decisions and future artifacts retain source/chunk/reference identifiers. Evidence is not replaced by model memory.

## Migration discipline
- Migrations are append-only and ordered.
- Repository migration head must be reconciled with the live database before release claims.
- Current verified repository/live head: 032 (2026-10-08).
- Schema changes require focused tests and an updated acceptance contract where lifecycle behavior changes.

## Lifecycle rule
Processing states must be durable and observable. Partial/draft artifacts cannot be presented as final approved knowledge.

## Related references
- docs/DATABASE.md
- docs/TESTING.md
- docs/PHASE_13_17_PREPARATION_PLAN.md
