# External Activation Runbook

> Owner: Production operations
> Update when: provider activation steps or external release gates change
> Last Updated: 2026-10-08
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
Paid LLM activation is intentionally deferred. When resumed, configure the OpenAI-compatible AI endpoint/model and embedding provider in backend secrets, then run the real provider E2E.

## Render
Reconcile live API/worker environment with the checked-in render.yaml, including DATABASE_URL and database-required mode. Live verification on 2026-10-08 confirmed the worker deployment policy is manual/off; the checked-in blueprint remains commit-triggered, so any intentional change must be explicitly re-verified.

## Netlify
Set public API/Supabase variables in the frontend environment and promote only after UI smoke, accessibility/performance and release gates pass.

## Evidence
Every external gate must record observed environment, revision, action, result and cleanup. Static code/config inspection alone is insufficient.
