# Cognix Nexus — Release Gate Matrix

> Owner: Release engineering
> Last Updated: 2026-10-08
> Secrets and secret values never belong in this file.

This file defines what can be automated now and what still requires an operator/browser/device.

## Automated / code-ready

| Gate | Runner | Operator input |
|---|---|---|
| AI + embeddings + extraction + RRF/citation | `scripts/provider_e2e.py` | AI/embedding credentials |
| Supabase Storage | `scripts/provider_e2e.py` | Supabase URL/service-role + bucket |
| Backblaze B2 | `scripts/provider_e2e.py` | B2 credentials |
| Google Drive | `scripts/provider_e2e.py` | OAuth client + account-owner refresh token |
| Backup/restore | `scripts/backup_restore_drill.py` | production DATABASE_URL for the real drill |
| Book schema/lifecycle contract | `scripts/book_acceptance_contract.py` | test/staging DATABASE_URL |
| Sentry ingestion probe | `scripts/sentry_live_check.py` | Sentry DSN; UI observation remains manual |
| Frontend typecheck/lint/build | CI | none |
| Backend compile/unit/integration | CI | none |
| Mobile config validation | CI | none |

## Operator/browser/device gates — intentionally last

These are not promoted to PASS from static code inspection:

1. Authenticated Playwright production smoke.
2. Full keyboard/screen-reader/responsive sweep.
3. Lighthouse/performance baseline.
4. Mobile EAS/device smoke.
5. Production backup/restore/rollback against the real environment.
6. GDPR export/delete against a real owner account.
7. Sentry live event ingestion.
8. Final production smoke and release approval.

## Key collection order

Provide values only when requested for a specific gate. Never paste them into the repository.

1. AI/embedding provider keys.
2. Supabase service-role credentials.
3. B2 credentials.
4. Google OAuth values and account-owner refresh token.
5. Sentry DSN.
6. Browser E2E test account.
7. Production DATABASE_URL only for the final recovery drill.

A preflight can be run first to show exactly which gate is runnable without printing values:
`python scripts/release_gate_preflight.py`.

## Evidence rule

A gate is PASS only when the real runner completes successfully and records:
- UTC timestamp
- revision
- gate name
- observed result
- cleanup result
- no secret values

Static code presence is READY, not PASS.
