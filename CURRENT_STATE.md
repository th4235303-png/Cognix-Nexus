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

## Production follow-up — 2026-10-21 UTC (security audit and resilient release health checks)

- **Dependency security:** CI's `pip-audit` identified 8 advisories in Pillow 12.3.0 (CVE-2026-112895, CVE-2026-112400, CVE-2026-112397, CVE-2026-112896, CVE-2026-112897, CVE-2026-112395, CVE-2026-112404, CVE-2026-112899). Updated `apps/web-platform/backend/requirements.lock` to Pillow 13.0.0. The subsequent backend CI run completed successfully and `pip-audit -r requirements.lock` reported **No known vulnerabilities found**. Dependency fix commit: `859b2d83af42220b14a4878553412f8e3e76a10f`.
- **Preflight test correction:** Added `COGNIX_WORKER_BASE_URL` to the release preflight test fixture so all gates can reach READY when every required input is supplied. Commit: `b3f3247b5b02e3f7bcccd08f667b1ce8fc116012`.
- **Release gate environment wiring:** Passed `COGNIX_API_BASE_URL` and `COGNIX_WORKER_BASE_URL` from GitHub secrets into the release-gate preflight job, avoiding false missing-variable reports. Commit: `fb1e0b58bd403753c1be7252a1215774aa90e1e2`.
- **Cold-start handling:** A live production health gate initially timed out on `/health` after 30 seconds while `/ready` subsequently returned HTTP 200 in ~14 seconds. Hardened `scripts/render_health_check.py` to retry transient network/timeouts and HTTP 5xx while failing fast on client-side 4xx, and added unit tests for timeout retry, server-error retry, and non-retryable 4xx. Commits: `88754aa3e2b21f773f95f634446c661922643458` and `071d44c16f86228f328d01b02da723778483da74`.
- **Automated worker release gate:** Added a production CI step that checks the live Worker `/health` response for `status=ok`, `persistence=postgresql`, and `database=true`, with bounded retries for cold starts. Commit: `3a411f9ce5c60971e5e22262216e84e84969c799`.
- **Live deploys:** API deploy `dep-dbc4v4rbc2fs73bali80` and Worker deploy `dep-dbc4v5lg1s2s7392rckg` succeeded on commit `fb1e0b58bd403753c1be7252a1215774aa90e1e2`, including the Pillow 13.0.0 dependency. Post-deploy Worker logs show `worker_started persistence=postgresql database_configured=True poll_seconds=2.0`; no fresh `DuplicatePreparedStatement` or application error was found in the checked window.
- **Latest production CI gate:** Run [39550887397](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39550887397) passed backend lint/compile/migration/tests, frontend build and service-role leak check, live API health/readiness, live Worker health/PostgreSQL persistence, and frontend HTTPS/HTML smoke. CodeQL on the same commit also passed.
- **Latest main CI:** Run [39550733535](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39550733535) completed successfully on all backend, frontend, and mobile jobs. Latest main CI run [39550887386](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/39550887386) also completed successfully on commit `3a411f9ce5c60971e5e22262216e84e84969c799`; CodeQL passed on the same commit. A docs-only checkpoint update followed at `8f7ba36`; its new CI run is queued, and the application/runtime code did not change in that docs-only commit.
- **Release decision remains CONDITIONAL.** Automated service-health gates and dependency audit now pass, but this does not substitute for authenticated production browser smoke, a real worker queued-job terminal-success proof, provider/fallback and storage round trips, production corpus/RAG acceptance, isolated production recovery, Sentry live probe, and any launch-required owner OAuth/mobile/accessibility/GDPR checks. Exact deployed-SHA final smoke is still required.
