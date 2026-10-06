# Cognix Nexus — Production Status

> Evidence-first status. A feature is not production-complete merely because its code exists.

## Snapshot — 2026-10-06

| Gate | Status | Evidence / next action |
|---|---|---|
| Main CI | 🟢 PASS | Verified CI #696 |
| API deploy | 🟢 LIVE | Render API is live on latest main revision 7287b682... |
| Worker | 🟢 LIVE | Render worker is live on latest main revision 7287b682... |
| Cloudinary | 🟢 VERIFIED | Live upload/read/checksum/delete completed |
| Supabase Storage | 🟡 CONFIGURED | Full provider drill still pending |
| B2 | 🟡 CONFIGURED | Full provider drill still pending |
| Embeddings | 🟡 CONFIGURED | Full real-provider drill pending |
| LLM | ⚪ DEFERRED | Paid provider activation intentionally postponed |
| Google Drive | ⚪ DEFERRED | OAuth/provider drill intentionally postponed |
| RLS cleanup | 🟢 VERIFIED | Migration 028 applied in production |
| Supabase security | 🟡 WARN | Leaked-password protection disabled; current free-tier account cannot enable it |
| Observability | 🟡 PARTIAL | Sentry hooks exist; live ingestion not verified |
| Netlify | 🟡 PENDING | UI completion/smoke gate remains |
| Cloudflare edge | 🟡 NOT DEPLOYED | No Cognix domain/zone available yet |
| GDPR delete/export | 🔴 OPEN | Full account lifecycle not verified |
| UI completion | 🟡 ACTIVE | P0.1→UI completion/polish is the current execution track |

## Database evidence

- Cognix migration ledger includes 028_rls_policy_dedup.
- 028 removed the redundant level-up deny policies.
- Supabase performance advisor no longer reports the previous redundant-policy warning set.
- Supabase security advisor still reports exactly one warning: auth_leaked_password_protection.
- The leaked-password warning is an account-level Auth limitation on the current free-tier plan, not an application-code defect.

## Runtime evidence

- Render API service: Cognix-Core, branch main, latest live deploy is revision 7287b682....
- Render worker service: cognix-core-worker-runtime, branch main, latest live deploy is revision 7287b682....
- Both services are on the latest repository revision available at the verification checkpoint.
- External web probing of /api/v1/health and /api/v1/ready was not available from the verification tool, so those two endpoints remain an explicit smoke item rather than being falsely marked PASS.

## Release track

The current track deliberately excludes paid LLM activation and Google Drive re-authorization. Those can be resumed later without reopening the engineering plan.

The current completion target is:
**P0 engineering → storage/processing verification → security regression → UI completion/polish → production smoke → release.**

## Release rule

Do not call the system fully production-ready until the remaining red/open engineering gates and final UI/release smoke are closed with real evidence.