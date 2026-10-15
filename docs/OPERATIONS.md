# Cognix Nexus — Operations

> Owner: Operations
> Update when: runtime operations, health semantics, queue/lease behavior, recovery, or observability changes
> Last Updated: 2026-10-15
> Do NOT put here: strategic roadmap or static architecture history.

## Runtime
Frontend: Render (`cognix-nexus-frontend`). API: Render (`Cognix-Core`). Worker: Render (`cognix-core-worker-runtime`). Persistence/Auth: Supabase/PostgreSQL. Netlify is legacy documentation, not the currently verified frontend host.

## Current evidence (2026-10-15)
- Revision `54be85aa883b589b392d14279ea73e830951a522` is deployed LIVE to API, worker and frontend.
- GitHub Cognix Core CI and CodeQL are green on this revision.
- API Render logs show repeated `GET /health 200 OK`.
- Worker Render logs show `worker_started persistence=postgresql database_configured=True`.
- Supabase migration tracker records migrations 034–041 as applied.
- A current post-deploy `/ready` response is not yet captured. Do not treat a historical readiness response as evidence for the current revision.

## Health semantics
- `/health` is liveness and does not require the database.
- `/ready` reports persistence readiness when database persistence is configured/required.
- Production should use `COGNIX_REQUIRE_DATABASE=true` so missing database bindings fail fast.
- Capture both endpoints after each release candidate; keep timestamp, revision, status and response body, but never include credentials.

## Worker operations
Worker jobs use durable leases/fencing and bounded retries. Inspect durable task state, lease fields, retry/backoff state and worker logs when a queue appears stuck. Confirm the worker starts against PostgreSQL and inspect task outcomes before claiming end-to-end processing success.

Export worker state transition is owned by the export service rather than an external synthetic task state.

## Release checks
Run frontend install/typecheck/lint/build and backend compileall/test discovery; then smoke authentication, upload limits, Brain Vault retrieval, worker processing, exports, health and readiness. CI green and a live deployment are necessary but not sufficient for release approval.

## Recovery
Stop promotion first. Restore the previous known-good application revision and preserve database compatibility. For database recovery, use an isolated restore drill or forward-compatible migration strategy. CI has a passing backup/isolated-restore drill; repeat against the intended production recovery target before final release.

## Observability and outstanding gates
Sentry hooks exist but live ingestion remains unverified. Provider, Google Drive export/retry/idempotency, authenticated browser/device, accessibility/performance, GDPR and final restore evidence must be captured before release status is promoted. Supabase Auth leaked-password protection is still a WARN and requires an explicit decision.
