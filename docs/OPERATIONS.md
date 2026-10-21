# Cognix Nexus — Operations

> Owner: Operations  
> Update when: runtime operations, health semantics, queue/lease behavior, recovery, or observability changes  
> Last Updated: 2026-10-21  
> Do NOT put here: strategic roadmap or static architecture history.

## Runtime and deployed revisions

- Frontend: Render `cognix-nexus-frontend` — latest deployment for `ee1288d9778dcadb3bfa3b183f856e7c5e5bfba6` is LIVE. This revision includes a documentation/checkpoint update; it does not change frontend runtime code.
- API: Render `Cognix-Core` — latest verified LIVE runtime deployment is `fb1e0b58bd403753c1be7252a1215774aa90e1e2`.
- Worker: Render `cognix-core-worker-runtime` — latest verified LIVE runtime deployment is `fb1e0b58bd403753c1be7252a1215774aa90e1e2`.
- Persistence/Auth: Supabase/PostgreSQL.
- Netlify references elsewhere in the repository may be legacy; Render is the currently verified frontend host.

## Latest CI evidence — 2026-10-21

- [Production release gate](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39551181681) passed: backend lint/compile/migration/tests, frontend production build and secret-leak check, live API health/readiness, live Worker health/PostgreSQL persistence, and frontend HTTPS/HTML smoke.
- [Main CI](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39551181572) passed backend, frontend, mobile, database integration, synthetic Book Intelligence contract, isolated backup/restore test, and dependency audit.
- [CodeQL](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39551181507) passed JavaScript/TypeScript and Python analysis.
- Backend dependency audit reports no known vulnerabilities after upgrading Pillow to 13.0.0.
- These are CI/service-health passes, not unconditional production authorization. The release decision remains CONDITIONAL pending external acceptance evidence.

## Health semantics

- API `/health` is liveness and does not require the database.
- API `/ready` reports persistence readiness when database persistence is configured/required.
- Production should use `COGNIX_REQUIRE_DATABASE=true` so missing database bindings fail fast.
- The automated production release gate checks API health/readiness, Worker `/health` with `status=ok`, `persistence=postgresql`, `database=true`, and frontend HTTPS/HTML response.
- Migration 045 adds `idx_agent_lifecycle_events_job_id` for the foreign key to `agent_jobs(id)` flagged by the Supabase performance advisor. Confirm it is applied after the next API/Worker startup migration.
- Render health checks retry transient timeouts/network errors and HTTP 5xx; client-side 4xx failures are not retried.
- Capture timestamp, revision, status and response body after each release candidate; never include credentials.

## Worker operations

- Worker starts with PostgreSQL persistence and polls on a two-second interval. Durable task leases/fencing and bounded retries are implemented.
- Queue selection now requires a real `binary_path` or `binary_storage` reference; filename-only orphan rows are no longer selected for processing. A regression test protects this contract. The existing failed synthetic book record is left untouched for explicit data-owner review.
- Latest verified worker startup log: `worker_started persistence=postgresql database_configured=True poll_seconds=2.0`.
- Database status aggregation on 2026-10-21 found four `processing_tasks` in `completed / needs_review`, one `failed / queued` task (a 403 fetching Wikipedia), one `books` row in `completed / ready`, and one failed synthetic E2E book (missing binary/path metadata). These old rows were not mutated. No active queued/running task was shown by that aggregate, and it does **not** demonstrate that a newly enqueued job reached terminal success.
- Inspect task lease fields, retry/backoff state and worker logs when a queue appears stuck. Do not retry or delete failed production records until their cause and idempotency implications are understood.
- The earlier `DuplicatePreparedStatement` error was addressed with Psycopg `prepare_threshold=None`; the latest checked deployment starts successfully. Keep monitoring for recurrence.
- Export worker state transitions are owned by the export service rather than an external synthetic task state.

## Database security

- All current public application tables have RLS enabled. User-facing tables use owner-scoped policies.
- Brain Soul/YouTube tables intentionally have no frontend policies and are restricted to backend/service-role access. Migration 044 revokes `anon` and `authenticated` table/sequence privileges for `brain_soul_context`, `brain_soul_syntheses`, `youtube_channels`, and `brain_youtube_videos`. Do not add broad client policies just to silence the RLS advisor.
- Supabase Auth leaked-password protection remains deferred under the current free-tier decision; enable it if plan/product scope permits.

## Release checks and outstanding acceptance gates

Before unconditional production sign-off, capture evidence for:
1. Authenticated production browser smoke: login, Supabase session, protected API call, and redirect/CORS behavior using a dedicated E2E account.
2. A real queued Worker job reaching successful terminal state with DB-backed processing and no prepared-statement error.
3. Provider E2E/fallback and storage upload/download round trips for Supabase Storage, Backblaze B2, and Cloudinary; verify the configured 1536-dimension Cohere embedding route.
4. Production Book Intelligence corpus acceptance against its isolated acceptance database; synthetic CI fixtures are not corpus acceptance.
5. Backup → isolated production-recovery-target restore → rollback drill.
6. Sentry live ingestion probe.
7. Fresh Google Drive owner OAuth consent plus export/retry/idempotency if in launch scope.
8. Mobile EAS/device smoke, accessibility/performance, and GDPR export/delete verification if release-required.
9. Final smoke against the exact candidate revisions before changing the verdict to Production Ready.

## Recovery

Stop promotion first. Restore the previous known-good application revision and preserve database compatibility. Use an isolated restore target for recovery validation; never run synthetic acceptance fixtures against the production database. CI's isolated backup/restore test passing does not replace a production recovery-target drill.

## Release rule

A configured secret, successful build, healthy process, or deployed service is not by itself a production PASS. Final PASS requires observed evidence on the exact release revision. Never record secret values in repository state or release documentation.
