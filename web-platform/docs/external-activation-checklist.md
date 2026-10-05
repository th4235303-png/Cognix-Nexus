# Cognix Core — External Activation Checklist

Never commit secret values.

## Storage roles — production target

| File type | Storage | Rule |
|---|---|---|
| Research images, covers, thumbnails | Cloudinary | <10 MB; media optimization |
| Small PDFs, notes, summaries | Supabase Storage | <=50 MB; private app artifacts |
| Large PDFs, EPUBs, research papers | Backblaze B2 | >50 MB; large originals |
| Export packages, backups | Google Drive | user-owned export/backup destination |

Book uploads use the tiered adapter: <=50 MB goes to Supabase Storage and >50 MB goes to Backblaze B2. Image ingestion uses Cloudinary with a 10 MB guard on the current free plan.


## Supabase Storage — derived artifacts
Set:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- COGNIX_SUPABASE_STORAGE_BUCKET=cognix-artifacts

Keep the bucket private and the service-role key backend-only.

## Google Drive — export/backup
Set:
- COGNIX_DRIVE_PROVIDER=google
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- GOOGLE_REFRESH_TOKEN
- GOOGLE_DRIVE_ROOT_FOLDER_ID (optional)

Authorize through /integrations/google-drive/authorize. The callback validates a signed, time-limited OAuth state and returns the refresh token once for operator-side secret storage. Never commit or share the token.

## Production AI
Set:
- COGNIX_PROCESSING_PROVIDER=ai
- COGNIX_AI_BASE_URL
- COGNIX_AI_API_KEY
- COGNIX_AI_MODEL

Configure the backend embedding provider as required by the deployed model provider.

## Frontend
Set:
- NEXT_PUBLIC_COGNIX_API_URL
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY

The frontend API client forwards the current Supabase access token when a session exists.

## Mobile
Set:
- EXPO_PUBLIC_COGNIX_API_URL

Production device builds still require Expo/EAS account and signing setup.

## Render
Production API and worker must share the same `DATABASE_URL` and provider credential bindings.
- Set `DATABASE_URL` on the live worker service (`cognix-core-worker-runtime`) as well as the API.
- Set `COGNIX_REQUIRE_DATABASE=true` on the live worker so a missing database binding fails fast instead of silently running in memory mode.
- The checked-in `render.yaml` declares these variables for the intended worker definition, but an existing live Render service must be reconciled manually if its configuration predates the blueprint.
The checked-in render.yaml defines the Python API, native Render worker, Cloudinary originals/media, private Supabase artifact storage, Backblaze B2 large-file storage, and Google Drive export boundary. The live Render API and worker must each have the Cloudinary, Supabase, B2, AI/embedding, and Google OAuth secrets bound.

If an existing Render service has a different resource type/root directory, reconcile it in the Render dashboard rather than creating duplicates.

## Netlify
netlify.toml builds from main. Set the public API/Supabase variables in Netlify production, then deploy the latest main commit.

## Final live drill
Use `web-platform/backend/scripts/provider_e2e.py` for the one-shot real-provider drill. A production run completed successfully on 2026-10-05 as `20261005-1800` and recorded `provider_e2e.completed` in Supabase. The proof covered Cloudinary upload/read/checksum, Supabase private artifact round-trip, B2 large-file round-trip, tiered book routing, extraction → chunks → 1536-dimension embeddings → owner-scoped RRF/RAG citation, Google Drive export/upsert retry, and owner isolation. Temporary E2E data was cleaned up, and the temporary Render E2E startup hook/run variable was removed/cleared.

This closes the **provider integration** E2E gate. The production paid LLM model is restored, but the latest live paid-model request returned HTTP 402 from OpenRouter, so paid-LLM availability remains an external credit/billing gate. Separate residual hardening items (isolated backup/restore proof, complete account export/delete lifecycle, Cloudflare edge deployment, observability provider activation, true two-session PostgreSQL concurrency proof, and the Supabase leaked-password-protection warning) remain tracked and are not represented as completed by this provider drill.
