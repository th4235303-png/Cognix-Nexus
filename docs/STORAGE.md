# Cognix Nexus — Storage

> Owner: Storage
> Update when: provider roles, routing thresholds, integrity rules, or backup/export behavior changes
> Last Updated: 2026-10-08
> Do NOT put here: secret values or live provider PASS claims without evidence.

## Production target

| File role | Provider | Rule |
|---|---|---|
| Research images/covers/thumbnails | Cloudinary | current media limit <10 MB |
| Small PDFs/notes/summaries | Supabase Storage | <=50 MB, private |
| Large PDFs/EPUBs/research papers | Backblaze B2 | >50 MB |
| Export packages/backups | Google Drive | user-owned destination |

Book uploads use the tiered adapter. Image ingestion uses Cloudinary. Provider secrets remain backend-only.

## Integrity

Storage writes should retain durable object references and checksums where supported. Retry/idempotency must not create silent duplicate durable state.

## Google Drive

Drive is the user-owned export/backup destination. OAuth/export implementation exists; real account authorization and provider verification remain pending/deferred.

## R2

An R2-compatible adapter exists in the repository, and historical completion material referenced R2 verification. The configured tiered storage target is Supabase Storage + B2. Therefore R2 is **optional/VERIFY**, not a current production dependency unless live configuration proves otherwise.

## Provider drills

Supabase Storage and B2 live write/read/checksum drills remain pending. Cloudinary round-trip evidence was previously observed.

## Backup

Production backup/restore/rollback remains an external release gate. Do not call an application-level rollback a database restore.
