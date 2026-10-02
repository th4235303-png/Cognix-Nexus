# Cognix Core — External Activation Checklist

Never commit secret values.

## Backblaze B2 — original files
Set on both API and worker:
- COGNIX_BOOK_STORAGE_PROVIDER=b2
- COGNIX_MEDIA_STORAGE_PROVIDER=b2
- COGNIX_B2_ENDPOINT
- COGNIX_B2_BUCKET
- COGNIX_B2_KEY_ID
- COGNIX_B2_APPLICATION_KEY
- COGNIX_B2_REGION=us-east-005

Verify with a real PDF/EPUB upload, storage round-trip, and SHA-256 comparison.

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
Production API and worker must share the same `DATABASE_URL`.
- Set `DATABASE_URL` on the live worker service (`cognix-core-worker-runtime`) as well as the API.
- Set `COGNIX_REQUIRE_DATABASE=true` on the live worker so a missing database binding fails fast instead of silently running in memory mode.
- The checked-in `render.yaml` declares these variables for the intended worker definition, but an existing live Render service must be reconciled manually if its configuration predates the blueprint.
The checked-in render.yaml defines the Python API, native Render worker, B2 originals, private Supabase artifact storage, and Google Drive export boundary.

If an existing Render service has a different resource type/root directory, reconcile it in the Render dashboard rather than creating duplicates.

## Netlify
netlify.toml builds from main. Set the public API/Supabase variables in Netlify production, then deploy the latest main commit.

## Final live drill
Run health/readiness, B2 round-trip, private artifact write/read, Google Drive export, processing idempotency/retry, agent lease/retry, RRF citation checks, local vault decrypt, isolated backup/restore, Expo device smoke test, and the 500-page stress workflow.
