# Cognix Nexus — Troubleshooting

> Owner: Operations/support
> Update when: recurring failure modes or recovery procedures change
> Last Updated: 2026-10-08
> Do NOT put here: unverified production status.

## CI failure
Check the latest main workflow run and failing job. Do not use an older green run as current release evidence.

## Queue stuck
Inspect durable processing/export task state, book/export lease fields, worker logs, retry/backoff state and the latest worker deployment revision.

## LLM 402
Verify provider quota/credit and configured base URL, API key and model in the runtime environment. Never paste secrets into chat or source control.

## Google invalid_scope
Re-authorize the Google OAuth client using the exact current Drive scope. Replace the stored refresh token after authorization and rerun the provider drill.

## RLS warning
Verify the production migration ledger first. Repository migration 032 does not prove the live database has reached 032.

## Storage mismatch
Check tier threshold, provider prefix, object checksum and durable DB reference before retrying.

## Security regression
Do not disable authentication/RLS to make an E2E pass. Fix owner context, policy or provider configuration.

## Worker deployment discrepancy
The checked-in Render blueprint indicates commit-triggered deployment, while prior live evidence recorded the worker as manual/off. Treat live state as VERIFY until independently observed.
