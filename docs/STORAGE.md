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
Storage writes retain durable object references and checksums where supported. Retry/idempotency must not create silent duplicate durable state.

## Google Drive
Drive is the user-owned export/backup destination. OAuth/export implementation exists; real account authorization and provider verification remain pending/deferred.

## R2 role — resolved
R2 is **not production-active in the current storage path**. The repository R2 adapter is explicitly backward-compatible/legacy, while current routing assigns small artifacts to Supabase Storage and large originals to Backblaze B2. The backend environment example also labels Cloudflare R2 compatibility as legacy optional.

## Provider drills
Supabase Storage and B2 live write/read/checksum drills remain pending. Cloudinary round-trip evidence was previously observed.

## Backup
Production backup/restore/rollback remains an external release gate. Do not call an application-level rollback a database restore.
