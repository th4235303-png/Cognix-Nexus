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
Repository migration head: 032.
Live Supabase migration head: **032**, verified 2026-10-08 against project `Cognix-Core` (`jarfusheiqkfcbeljvhj`) using live migration history. The live history includes `031_book_intelligence_safe` and `032_phase7_12_hardening`.

Evidence: Supabase project migration history was queried live on 2026-10-08.

### Confirmed migration numbering defect
Two historical migrations use the 010 number:
- 010_agent_active_layer.sql
- 010_intelligence_life_reliability.sql

Do not silently rename either migration during documentation migration.

## Book Intelligence extension
Durable processing/knowledge state includes immutable book versions/fingerprints, duplicate matches, progress snapshots, append-only reading events, source-linked knowledge items, versioned chapter/book summaries, lesson packs, derived books/synthesis projects and Markdown/plain-text reading ledgers.

Invariants: exact duplicates stop; interrupted work resumes; partial knowledge remains partial; every knowledge item traces to source spans; cross-book synthesis preserves contributing versions/disagreement; originals remain separate; reprocessing creates a new version.

## Resolved verification
- Live Supabase migration head is 032, verified 2026-10-08.
- Current Secret Vault KDF implementation is PBKDF2-SHA256 with 600,000 iterations and AES-GCM in the browser; the historical Argon2id wording is not the current implementation.
