# Cognix Nexus — Production Status

> Evidence-first status. A feature is not production-complete merely because its code exists.

## Snapshot — 2026-10-06

| Gate | Status | Evidence / next action |
|---|---|---|
| Main CI | 🟢 PASS | Run #696 on main |
| API deploy | 🟡 LIVE | Current Render live deploy is older than latest main; redeploy/verify |
| Worker | 🟡 LIVE | Current Render worker deploy is older than latest main; redeploy/verify |
| Cloudinary | 🟢 VERIFIED | Live upload/read/checksum/delete completed |
| Supabase Storage | 🟡 CONFIGURED | Full provider drill still pending |
| B2 | 🟡 CONFIGURED | Full provider drill still pending |
| Embeddings | 🟡 CONFIGURED | Real provider drill pending |
| LLM | 🔴 BLOCKED | Live provider configuration/402 |
| Google Drive | 🔴 BLOCKED | Live OAuth scope/configuration issue |
| RLS cleanup | 🟡 PENDING | Production ledger stops at 027; 028 not yet applied |
| Supabase security | 🟡 WARN | Leaked-password protection disabled |
| Observability | 🟡 PARTIAL | Sentry hooks exist; live ingestion not verified |
| Netlify | 🟡 PAUSED | Intentional release safeguard |
| Cloudflare edge | 🟡 NOT DEPLOYED | No Cognix zone/edge deployment verified |
| GDPR delete/export | 🔴 OPEN | Full account lifecycle not verified |

## CI evidence
- Latest main run: Cognix Core CI #696.
- Result: success.
- Unit/integration/coverage/security/backup-restore gates are represented in CI.

## Database evidence
- Custom Cognix migration ledger currently reaches 027_rls_helper_performance.sql.
- Migration 028_rls_policy_dedup.sql exists in the repository but is not yet recorded in production.
- Supabase performance advisor still reports 176 multiple-permissive-policy warnings from redundant policies.
- Supabase security advisor reports leaked password protection disabled.

## Release rule
Do not call the system fully production-ready until the red gates and the pending production verification gates above are closed with real evidence.