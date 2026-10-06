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