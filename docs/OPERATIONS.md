# Cognix Nexus — Operations

> Owner: Operations
> Update when: runtime operations, health semantics, queue/lease behavior, recovery, or observability changes
> Last Updated: 2026-10-08
> Do NOT put here: strategic roadmap or static architecture history.

## Runtime
Frontend: Netlify. API/worker: Render. Persistence/Auth: Supabase/PostgreSQL.

## Health semantics
- /health is liveness and does not require the database.
- /ready reports persistence readiness when database persistence is configured/required.
- Production should use COGNIX_REQUIRE_DATABASE=true so missing database bindings fail fast.

## Worker operations
Worker jobs use durable leases/fencing and bounded retries. Inspect durable task state, lease fields, retry/backoff state and worker logs when a queue appears stuck.

Export worker state transition is owned by the export service rather than an external synthetic task state.

## Release checks
Run frontend install/typecheck/lint/build and backend compileall/test discovery, then smoke authentication, upload limits, Brain Vault retrieval, worker processing, exports, health and readiness.

## Recovery
Stop promotion first. Restore the previous known-good application revision and keep database compatibility. For database recovery, use an isolated restore drill or forward-compatible migration strategy.

## Observability
Sentry hooks exist but live ingestion remains VERIFY. Provider, browser/device and restore evidence must be captured before release status is promoted.
