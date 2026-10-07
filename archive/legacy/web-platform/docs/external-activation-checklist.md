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

Google Drive integration is implemented in the backend; the real-account provider drill is the remaining external activation step. The feature is not removed from the plan. When you are ready to re-authorize Drive, set:
- COGNIX_DRIVE_PROVIDER=google
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- GOOGLE_REFRESH_TOKEN
- GOOGLE_DRIVE_ROOT_FOLDER_ID (optional)

Authorize through /integrations/google-drive/authorize. The callback validates a signed, time-limited OAuth state and returns the refresh token once for operator-side secret storage. The export worker creates/upserts the package folder/files and is designed for crash-safe idempotent retry. Never commit or share the token.

## Production AI

Paid LLM activation is intentionally deferred. It is not a current P0 release blocker.

When resumed, set:
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

Production API and worker must share the same DATABASE_URL and provider credential bindings.
- Set DATABASE_URL on the live worker service as well as the API.
- Set COGNIX_REQUIRE_DATABASE=true on the live worker so a missing database binding fails fast instead of silently running in memory mode.
- The checked-in render.yaml declares these variables for the intended worker definition, but an existing live Render service must be reconciled manually if its configuration predates the blueprint.

## Netlify

netlify.toml builds from main. Set the public API/Supabase variables in Netlify production, then deploy the latest main commit. Final public release remains gated on UI smoke and release verification.

## Provider drill

web-platform/backend/scripts/provider_e2e.py remains the one-shot provider drill for when external providers are intentionally enabled. The current release evidence claims implementation and persisted embedding state, but does not fabricate a real provider PASS where credentials have not been exercised.

Previously verified evidence remains valid for the components actually observed, including the live Cloudinary upload/read/checksum/delete round-trip.

## Known account-level limitation

Supabase currently reports leaked-password protection disabled. The active project is on the free tier, so this Auth feature cannot be enabled on the current plan. Keep the warning documented and do not represent it as an application-code failure.

## Final activation rule

Use PRODUCTION_STATUS.md for verified evidence, REMAINING_WORK.md for execution, UI_PLAN.md for UI requirements and UI_STATUS.md for UI verification. All implementation and documentation changes land on main.
