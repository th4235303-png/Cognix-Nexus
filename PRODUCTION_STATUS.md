# Cognix Nexus — Production Status

> Evidence-first status. A feature is not production-complete merely because its code exists.

## Snapshot — 2026-10-06

| Gate | Status | Evidence / next action |
|---|---|---|
| Main CI | 🟢 PASS | Verified CI #696 |
| API deploy | 🟡 DEPLOYING | Security-hardened retrieval/export code is queued in Render deploy 5398929...; final live confirmation follows deployment completion. |
| Worker | 🟡 DEPLOYING | Worker deploy 5398929... is in progress after the P0 security hardening. |
| Cloudinary | 🟢 VERIFIED | Live upload/read/checksum/delete completed |
| Supabase Storage | 🟡 CONFIGURED | Full private write/read/checksum provider drill still pending |
| B2 | 🟡 CONFIGURED | Full large-file write/read/checksum provider drill still pending |
| Embeddings | 🟡 CONFIGURED | Production DB has 101 persisted 1536-d vectors; live provider/API drill remains pending |
| LLM | ⚪ DEFERRED | Paid provider activation intentionally postponed |
| Google Drive | 🟡 IMPLEMENTED / EXTERNAL DRILL PENDING | OAuth, refresh-token, export worker, folder/upsert/idempotent retry code exists; real account drill awaits credentials re-authorization |
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
- Supabase performance advisor no longer reports the previous redundant-policy warning set.\n- Production processing snapshot: 2 books, 61 chapters, 101 chunks, 101 embeddings; queued=0 and running=0; all observed embedding vectors are 1536-dimensional.\n- The P0 60-page test book contains 60 chapters, 100 chunks and 100 embeddings; one historical failed processing task remains preserved.
- Supabase security advisor still reports exactly one warning: auth_leaked_password_protection.
- The leaked-password warning is an account-level Auth limitation on the current free-tier plan, not an application-code defect.

## Runtime evidence

- Render API service: Cognix-Core, branch main, latest live deploy is revision d0c6d5bd....
- Render worker service: cognix-core-worker-runtime, branch main, latest live deploy is revision d0c6d5bd....
- Both services are on the latest repository revision available at the verification checkpoint.
- External web probing of /health and /ready was not reachable from the available verification tool, so those two endpoints remain an explicit smoke item rather than being falsely marked PASS.
- P0 owner-isolation hardening was added to hybrid RRF retrieval, Brain Vault export, and contradiction candidate/review paths; regression contract coverage was added.

## Release track

The current track deliberately excludes paid LLM activation and Google Drive re-authorization. Those can be resumed later without reopening the engineering plan.

The current completion target is:
**P0 engineering → external provider verification → security regression → UI completion/polish → production smoke → release.**

Code-level P0 security hardening is complete on main; credential-dependent provider drills remain explicitly open rather than being fabricated as PASS.

## Release rule

Do not call the system fully production-ready until the remaining red/open engineering gates and final UI/release smoke are closed with real evidence.