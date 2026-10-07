# Cognix Nexus — Data Model

## Ownership
User-owned records carry owner_id or are reachable through an owner-scoped parent. Legacy ownerless records fail closed for authenticated user access.

## Core lineage
source → book → chapter → chunk → embedding
source → review/claim/report
book/note/concept → graph relationships
agent job → run → finding → human review
export job → Google Drive package

## Security-sensitive records
- Vault items store ciphertext, nonce, KDF metadata; plaintext stays client-side.
- Time capsules/legacy payloads follow the encrypted-payload boundary.
- Mood data is local-only by policy.

## RLS
- Owner-scoped policies exist across core Brain Vault and Level Up user-data tables.
- Relationship tables are scoped through their owning parent where appropriate.
- Deny-by-default remains the baseline for tables without frontend access.
- Migration 028 removes redundant deny policies; production application is still pending.

## Migration discipline
Schema changes are registered through the Cognix migration ledger and verified in CI before production promotion.

## Book Intelligence extension

The existing `book → chapter → chunk → embedding` lineage is extended with durable reading and distillation state.

Planned records:

- **book_versions** — immutable processing/version identity, content fingerprint and source reference.
- **book_duplicate_matches** — exact/possible duplicate result, matched version, confidence and resolution.
- **book_progress_snapshots** — stage, completed/total units, percentage, current chapter/page, checkpoint and timestamps.
- **reading_events** — append-only extraction, chapter completion, retry, quota-pause and synthesis milestones.
- **knowledge_items** — distilled principles, concepts, definitions, examples, actions and insights with source-span lineage.
- **chapter_summaries / book_summaries** — versioned partial/final summaries; historical versions are never silently overwritten.
- **lesson_packs** — category/topic synthesis from multiple books.
- **derived_books / synthesis_projects** — generated study/lesson books with contributing source/version manifest.
- **reading_ledgers** — human-readable Markdown/plain-text history of date, book, category, progress and extracted keys.

### Invariants

1. Exact duplicates do not start another expensive reading run.
2. Interrupted jobs resume from the latest valid checkpoint.
3. Partial knowledge is labeled partial/draft and never represented as final synthesis.
4. Every knowledge item can trace back to source spans.
5. Cross-book synthesis preserves all contributing books/versions and disagreement.
6. Originals remain separate from derived knowledge.
7. Re-processing creates a new version instead of mutating historical evidence.
