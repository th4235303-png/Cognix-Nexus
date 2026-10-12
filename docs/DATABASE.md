# Cognix Nexus — Database

> Owner: Database/schema
> Update when: schema, migration ledger, RLS, ownership or lineage rules change
> Last Updated: 2026-10-12
> Do NOT put here: live release status unless it is directly a schema fact.

## Persistence
Production persistence targets PostgreSQL/Supabase with pgvector and Supabase Auth.

## Ownership
User-owned records carry owner_id or are reachable through an owner-scoped parent. Legacy ownerless access fails closed.

## Core lineage
source → book → chapter → chunk → embedding
source → review/claim/report
book/note/concept → graph relationships
agent job → run → finding → human review
export job → Google Drive package

## Security-sensitive records
Vault items store ciphertext, nonce and KDF metadata; plaintext remains client-side. Time capsules/legacy payloads follow the encrypted-payload boundary. Mood data is local-only by policy.

## RLS
Owner-scoped policies exist across core Brain Vault and Level Up user-data tables. Relationship tables are scoped through their owning parent where appropriate. Deny-by-default remains the baseline for tables without frontend access.

Migration `033_rls_policy_initplan_indexes` wraps the owner-policy JWT claim lookup in a scalar subquery on seven owner-scoped tables while preserving the same owner comparison and deny-by-default behavior. It also adds `idx_knowledge_items_chapter_id`.

## Migration state
Repository migration head: 033.
Live Supabase migration head: **033**, verified 2026-10-12 against project `Cognix-Core` (`jarfusheiqkfcbeljvhj`). Live history records migration `033_rls_policy_initplan_indexes` with version `20261012034910`.

Evidence: Supabase project migration history queried live on 2026-10-12.

### Confirmed migration numbering defect
Two historical migrations use the 010 number:
- 010_agent_active_layer.sql
- 010_intelligence_life_reliability.sql

Do not silently rename either migration during documentation migration.

## Book Intelligence extension
Durable processing/knowledge state includes immutable book versions/fingerprints, duplicate matches, progress snapshots, append-only reading events, source-linked knowledge items, versioned chapter/book summaries, lesson packs, derived books/synthesis projects and Markdown/plain-text reading ledgers.

Invariants: exact duplicates stop; interrupted work resumes; partial knowledge remains partial; every knowledge item traces to source spans; cross-book synthesis preserves contributing versions/disagreement; originals remain separate; reprocessing creates a new version.

## Live advisor verification — 2026-10-12
- Supabase performance advisor no longer reports the seven owner-policy `auth_rls_initplan` findings.
- Supabase performance advisor no longer reports the unindexed `knowledge_items.chapter_id` foreign key.
- Remaining performance notices are INFO-level unused-index findings; do not drop indexes without workload evidence.
- Separate security warning remains: Supabase Auth leaked-password protection is disabled and must be enabled/verified in Auth settings.

## Resolved verification
- Live Supabase migration head is 033, verified 2026-10-12.
- Current Secret Vault KDF implementation is PBKDF2-SHA256 with 600,000 iterations and AES-GCM in the browser; the historical Argon2id wording is not the current implementation.
