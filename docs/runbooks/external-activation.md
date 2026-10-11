# External Activation Runbook

> Owner: Production operations
> Update when: provider activation steps or external release gates change
> Last Updated: 2026-10-11
> Do NOT put here: secret values.

## Rules
Never commit or paste secret values into the repository, issues or chat.

## Supabase Storage
Configure the backend Supabase URL/service role and private artifacts bucket. Run the real write/read/checksum drill and record evidence before marking the provider VERIFIED.

## Backblaze B2
Configure backend B2 credentials and bucket. Run a >50 MB large-file write/read/checksum drill. Clean up test objects and record evidence.

## Google Drive
Use the backend Google authorization endpoint. The account owner must consent and produce the refresh token. Store it only in the backend secret environment. Run an idempotent export/upsert drill and record evidence.

## AI provider
LLM endpoints and model IDs are code-defined in `app/services/llm.py`; do not add endpoint/model overrides to Render. Provider keys enable optional routes. `COHERE_API_KEY` is currently required for the AI release-gate preflight because the persisted database schema uses `vector(1536)` and Cohere `embed-v4.0` is the only configured embedding route compatible with that dimension. Other embedding providers currently declare incompatible dimensions and must not be enabled for production writes without a coordinated migration/re-embedding plan. Run the real provider E2E and record each provider's observed result; configured keys alone are not evidence of success.

## Render
Live API service `Cognix-Core` (`srv-dauh0tu0tbcc73fdds2g`) and worker `cognix-core-worker-runtime` (`srv-dav13vm0tbcc73d4ek8g`) were observed on commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae` on 2026-10-11. The API uses commit-triggered deployment while the worker is manual/off. The checked-in `render.yaml` declares different service names/root directories and commit-triggered worker deployment, so live-vs-blueprint drift remains OPEN. Reconcile it deliberately; do not blindly sync the blueprint or change deploy policy.

Environment-variable cleanup is also OPEN: first inventory the actual live variable names, then remove only verified-unused model/URL/legacy routing overrides. Preserve provider credentials and all database/auth/storage/Google/E2E/recovery/release-gate settings. The current connected Render action cannot enumerate or delete individual variables, so do not use replace-all without a complete verified environment inventory.

## Netlify
Set public API/Supabase variables in the frontend environment and promote only after UI smoke, accessibility/performance and release gates pass.

## Evidence
Every external gate must record observed environment, revision, action, result and cleanup. Static code/config inspection alone is insufficient.
