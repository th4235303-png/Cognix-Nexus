# Authoritative Release Checkpoint — 2026-10-21

**Release Decision: Conditional Production Sign-Off — core runtime/CI green; final external acceptance evidence still required.**

## Latest verified state

- FastAPI production API: previously verified `GET /health = 200` and `GET /ready = 200` with PostgreSQL reachable.
- Next.js production frontend: previously verified HTTP 200 and deployed with explicit production API/Supabase configuration.
- Backend, frontend, and mobile CI suites are green on the latest verified release sequence.
- Worker PostgreSQL transaction-pooler compatibility was explicitly fixed with Psycopg `prepare_threshold=None`; the post-fix deployment emitted `worker_started persistence=postgresql database_configured=True` and the checked post-deploy log window contained no new `DuplicatePreparedStatement` traceback.
- Supabase migration 044/RLS/service-managed access boundaries remain verified as documented. Supabase Auth leaked-password protection remains explicitly accepted/deferred under the current free-tier policy and is not a blocker.

## Release-gate hardening completed

- Added `worker_health` to `scripts/release_gate_preflight.py` so selecting the Worker health gate now actually validates `COGNIX_WORKER_BASE_URL` instead of silently skipping that gate.
- Release workflow already exposes explicit provider, Book Intelligence, authenticated browser, Sentry, recovery, Render API health, and Worker health switches in `.github/workflows/release-gates.yml`.
- The Worker health gate validates HTTP `/health`, `status=ok`, `persistence=postgresql`, and `database=true` without printing secrets.
- Latest hardening commit: `e690418c65409175581573e37f309dbfb90fb055`.

## Evidence still required before unconditional green

1. Run the authenticated production Playwright smoke with a dedicated E2E account.
2. Run a real worker queued-job completion and retain evidence that the job reaches a successful terminal state without the prepared-statement error.
3. Run the provider E2E matrix using production-safe secrets; verify at least one healthy LLM route, required 1536-dimension Cohere embedding, and storage round trips for Supabase Storage, Backblaze B2, and Cloudinary.
4. Run production Book Intelligence corpus acceptance against its isolated acceptance database; synthetic CI coverage is not corpus acceptance.
5. Run the production backup → isolated restore → rollback drill.
6. Run the Sentry live ingestion probe.
7. Verify the final revision's public Supabase auth redirect/CORS behavior with the authenticated browser flow.
8. Complete Google Drive export/retry/idempotency using fresh owner OAuth consent if the integration is in launch scope.
9. Complete mobile EAS/device smoke, accessibility/performance checks, and GDPR export/delete verification if those are release-required.
10. Perform one final smoke against the exact release revision and only then change the verdict to unconditional Production Ready.

## Explicitly deferred / not blockers

- Supabase Auth leaked-password protection on the current free-tier plan.
- Google Drive fresh owner consent when treated as post-launch/client action.
- Paid LLM activation and optional infrastructure adoption unless the release scope changes.

## Release rule

A configured secret, successful build, or deployed service is not by itself a production PASS. Final PASS requires observed evidence on the exact release revision. Never record secret values in repository state or release documentation.
