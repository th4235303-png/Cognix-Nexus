# Cognix Nexus — Troubleshooting

> Owner: Operations/support
> Update when: recurring failure modes or recovery procedures change
> Last Updated: 2026-10-11
> Do NOT put here: unverified production status.

## CI failure
Check the latest main workflow run and failing job. Do not use an older green run as current release evidence.

## Queue stuck
Inspect durable processing/export task state, book/export lease fields, worker logs, retry/backoff state and the latest worker deployment revision.

## LLM 402
Verify provider quota/credit and the relevant provider API key. Endpoints and model IDs are code-defined in `app/services/llm.py`; do not try to fix routing by adding Render URL/model overrides. For embedding failures, confirm `COHERE_API_KEY` is present and remember production storage is fixed at 1536 dimensions. Never paste secrets into chat or source control.

## Google invalid_scope
Re-authorize the Google OAuth client using the exact current Drive scope. Replace the stored refresh token after authorization and rerun the provider drill.

## RLS warning
Verify the production migration ledger first. The repository and live Supabase migration heads were both verified at 032 on 2026-10-08; re-check the live migration head before final release.

## Storage mismatch
Check tier threshold, provider prefix, object checksum and durable DB reference before retrying.

## Security regression
Do not disable authentication/RLS to make an E2E pass. Fix owner context, policy or provider configuration.

## Worker deployment discrepancy
On 2026-10-11 the live API was commit-triggered and the live worker was manual/off, while `render.yaml` declares commit-triggered worker deployment and different service names/root directories. This drift is OPEN. Reconcile intentionally; do not blindly sync the blueprint or change deploy policy.
