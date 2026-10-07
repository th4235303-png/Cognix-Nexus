# Cognix Nexus — Database

> Owner: Database/schema
> Update when: schema, migration ledger, RLS, ownership or lineage rules change
> Last Updated: 2026-10-08
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

## Migration state
Repository head: 032. Live head: VERIFY. Repository migration presence does not prove the live database has reached 032.

### Confirmed migration numbering defect
Two historical migrations use the 010 number:
- 010_agent_active_layer.sql
- 010_intelligence_life_reliability.sql

Do not silently rename either migration during documentation migration.

## Book Intelligence extension
Durable processing/knowledge state includes immutable book versions/fingerprints, duplicate matches, progress snapshots, append-only reading events, source-linked knowledge items, versioned chapter/book summaries, lesson packs, derived books/synthesis projects and Markdown/plain-text reading ledgers.

Invariants: exact duplicates stop; interrupted work resumes; partial knowledge remains partial; every knowledge item traces to source spans; cross-book synthesis preserves contributing versions/disagreement; originals remain separate; reprocessing creates a new version.

## VERIFY
- Live migration head.
- Secret Vault KDF implementation: source documentation contains a PBKDF2 vs Argon2id discrepancy requiring actual verification.
