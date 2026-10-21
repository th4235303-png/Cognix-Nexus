# Cognix Nexus — Database

> Owner: Database/schema
> Update when: schema, migration ledger, RLS, ownership or lineage rules change
> Last Updated: 2026-10-21
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
All current public application tables have RLS enabled. User-facing tables have owner-scoped policies; service-managed Brain Soul/YouTube tables intentionally have no frontend policies and are restricted to backend/service-role access. Deny-by-default remains the baseline for tables without frontend access.

## Migration state
The application-managed `public.cognix_schema_migrations` registry is applied through migration `045_agent_lifecycle_events_job_index.sql` in production. Migration 044 revokes `anon` and `authenticated` table/sequence privileges for `brain_soul_context`, `brain_soul_syntheses`, `youtube_channels`, and `brain_youtube_videos`, and revokes those grants by default for newly-created public tables/sequences.

Migration 045 adds a covering index on `agent_lifecycle_events(job_id)` for the foreign key to `agent_jobs(id)` identified by the Supabase performance advisor. This is additive and does not alter access policies or data.\n\nThe separate Supabase CLI migration history remains at the historical `033_rls_policy_initplan_indexes` head. These are two different ledgers and must not be treated as interchangeable. The application migration runner is authoritative for the backend's ordered SQL migration set through 044.

### Confirmed migration numbering defect
Two historical migrations use the 010 number:
- 010_agent_active_layer.sql
- 010_intelligence_life_reliability.sql

Do not silently rename either migration.

## Book Intelligence extension
Durable processing/knowledge state includes immutable book versions/fingerprints, duplicate matches, progress snapshots, append-only reading events, source-linked knowledge items, versioned chapter/book summaries, lesson packs, derived books/synthesis projects and Markdown/plain-text reading ledgers.

Invariants: exact duplicates stop; interrupted work resumes; partial knowledge remains partial; every knowledge item traces to source spans; cross-book synthesis preserves contributing versions/disagreement; originals remain separate; reprocessing creates a new version.

## Live schema verification — 2026-10-16
- Production contains the full public application schema, including Brain Soul and YouTube tracker tables.
- All current public tables have RLS enabled.
- User-facing tables have active policies; the four service-managed Brain Soul/YouTube tables intentionally have zero frontend policies and no `anon`/`authenticated` table or sequence privileges.
- Migration 044 is recorded in `public.cognix_schema_migrations` with an applied timestamp and has been verified by read-only privilege queries. Migration 045 is applied by the API/worker startup migration runner after deployment.
- Supabase Auth leaked-password protection remains disabled. Per the current release decision, this free-tier/provider limitation is explicitly accepted and is not a database migration blocker.

## Resolved verification
- The previous 033-only database documentation is superseded by the application migration registry through 044.
- Supabase performance findings for the seven owner-policy `auth_rls_initplan` cases and the `knowledge_items.chapter_id` foreign key were previously remediated.
- Remaining performance notices are INFO-level unused-index findings; do not drop indexes without workload evidence.
- Secret Vault implementation remains PBKDF2-SHA256 with 600,000 iterations and AES-GCM in the browser; the historical Argon2id wording is not the current implementation.
