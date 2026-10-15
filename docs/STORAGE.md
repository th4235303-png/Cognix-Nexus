# Cognix Nexus — Storage

> Owner: Storage
> Update when: provider roles, routing thresholds, integrity rules, or backup/export behavior changes
> Last Updated: 2026-10-15
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

Drive is the user-owned export/backup destination. OAuth/export implementation exists, but the release gate still requires a real export, retry and idempotency verification against the intended OAuth account and root folder.

## R2 / Cloudflare role

R2 is **not production-active in the current storage path**. The repository R2 adapter is backward-compatible/legacy, while current routing assigns small artifacts to Supabase Storage and large originals to Backblaze B2. The 2026-10-15 Cloudflare account audit found no active R2 bucket because R2 is not enabled on the connected account. Do not move production traffic to R2 without an explicit architecture decision and provider drill.

## Provider drills

Historical evidence exists for Supabase Storage, B2 and Cloudinary, but the final release revision requires fresh evidence when release policy calls for it. The 2026-10-15 audit did not convert historical evidence into a new PASS.

## Backup

Production backup/restore/rollback remains an external release gate. Do not call an application-level rollback a database restore. The dedicated Supabase restore-drill project is healthy and should be used for isolated recovery verification.
