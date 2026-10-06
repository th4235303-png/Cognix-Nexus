# Cognix Nexus — Troubleshooting

## CI failure
Check the latest main workflow run and failing job first. Do not mark the release green from an older successful run.

## Queue stuck
Inspect processing_tasks, book/export lease fields, worker logs, retry/backoff state, and the latest worker deploy revision.

## LLM 402
Verify provider account credit/quota and the configured base URL, API key and model in the Render environment. Never paste secrets into chat or source control.

## Google invalid_scope
Re-authorize the Google OAuth client using the exact Drive scope expected by the current backend. Replace the stored refresh token after authorization and rerun the provider drill.

## RLS warning
First verify the production migration ledger. If 028 is absent, do not assume the repository migration has reached production.

## Storage mismatch
Check the storage tier threshold, provider prefix, object checksum and durable DB reference before retrying.

## Security
Do not disable authentication/RLS to make an E2E pass. Fix the owner context, policy or provider configuration instead.