# Current verification update — 2026-10-16

This section supersedes conflicting historical status below. Use the GitHub `main` branch head for the current revision; the live-health evidence below was captured by GitHub Actions on commit `0766ae7144f7a4e2c04bbeb74a8dcc96bec8acfa`, before the latest workflow-notice-only update.

- Repository structure and dependency/test fixes are committed to `main`; the latest Production CI run with live health verification passed on the evidence commit above. A newer run is in progress after a status-message-only workflow update.
- The Production CI pipeline now calls the real Render API `/health` and `/ready` endpoints on non-PR runs. Evidence: both returned HTTP 200; `/ready` reported `database_configured=true`, `database_reachable=true`, and `persistence_mode=postgresql`.
- A new migration `044_restrict_service_managed_brain_soul_youtube.sql` was registered and deployed. The application migration registry in `public.cognix_schema_migrations` confirms migrations through `044`; this is distinct from the separate Supabase CLI migration history, which still reports `033`.
- Migration 044 removes `anon` and `authenticated` table privileges and sequence privileges from `brain_soul_context`, `brain_soul_syntheses`, `youtube_channels`, and `brain_youtube_videos`; it also revokes those grants by default for future tables/sequences created by the migration role. Read-only privilege checks after deployment returned no grants for those roles.
- Render API deploy `dep-db8u9ubrjlhs73dirt80` is live and includes migration 044. Worker deploy `dep-db8uarqvcj2c73b8hkgg` is live and starts with `persistence=postgresql database_configured=true`. Frontend remains live on its latest frontend build.
- Supabase security advisor still reports leaked-password protection disabled (WARN). Four service-managed tables still produce the RLS-without-policy INFO finding; they have no Data API grants and are intentionally service-role/backend-only.
- Release remains **BLOCKED** until production backup/restore evidence is verified, leaked-password protection is enabled or an explicit exception is approved, and the remaining provider/authenticated acceptance checks are completed. Passing CI and live health checks alone are not release authorization.


## Repository

- Canonical active application paths are `apps/web-platform/frontend` and `apps/web-platform/backend`.
- `apps/mobile` is the reserved mobile product surface.
- `archive/legacy` is historical/reference material and is not active runtime code.
- `docs/REPOSITORY_STRUCTURE.md` documents the canonical layout; the repository Git tree is the authoritative path inventory.

## Render

- Connected workspace: `Cognix Core`.
- API: `https://cognix-core-ypak.onrender.com`; latest observed deploy for migration 044 is live at `446356556b5a3b8f42e4dc66e5803e984b43b88c`.
- Worker: `https://cognix-core-worker-runtime.onrender.com`; latest observed deploy is live at `c0ab03003ab50d3f8537cadce28d6d75995414d2`.
- Frontend: `https://cognix-nexus-frontend.onrender.com`; latest observed frontend deployment is live at `16d923a41179cae50c73ed64e8a1af07275b85a4`.
- API live verification from GitHub Actions: `/health` HTTP 200; `/ready` HTTP 200; database configured and reachable; PostgreSQL persistence mode. The live check is now part of Production CI.
- Render dashboard service paths still use legacy aliases (`web-platform/backend` and `cd web-platform/frontend` in the frontend build command) while `render.yaml` documents canonical `apps/web-platform/...` paths. Current services are live through the compatibility symlink; migrate service settings to canonical paths when the connected Render control surface permits it.

## Supabase

- Production project: `Cognix-Core` (`jarfusheiqkfcbeljvhj`), region `ap-southeast-1`, status `ACTIVE_HEALTHY`.
- Supabase CLI migration history still ends at 033; the application-managed `public.cognix_schema_migrations` registry is confirmed through 044. Do not treat these two registries as the same history.
- Migration 044 is applied through the live API deployment. Read-only checks confirmed no table or sequence privileges for `anon` or `authenticated` on the four service-managed Brain Soul/YouTube tables.
- Security advisor: leaked-password protection remains a WARN. The four RLS-without-policy INFO findings remain; those tables are intended for backend/service-role access, with Data API grants revoked.
- The CI backup/restore drill is isolated test evidence, not a verified production backup-and-restore drill.


## Remaining work — required before release

1. Verify the latest workflow run after the most recent status/documentation updates; the preceding Production CI run passed build, backend checks, and live `/health` + `/ready`.
2. Enable Supabase Auth leaked-password protection or record an explicitly approved exception.
3. Complete a production backup → isolated restore → rollback drill; CI's isolated drill is not a substitute.
4. Reconcile live environment-variable **names** against code, `render.yaml`, CI, recovery and test workflows without exposing secret values.
5. Confirm production frontend domain/TLS, API URL, Supabase public configuration and auth redirect URLs.
6. Decide whether to migrate the Render dashboard service paths from the compatibility bridge to canonical `apps/web-platform/...` paths.
7. Decide whether Vercel/Netlify remain intentionally unused; Render is the currently observed frontend host.
8. Review unused indexes using actual query-plan/usage evidence; delete none automatically.
9. Re-run Cloudinary fresh round-trip evidence if required by release policy.
10. Prove Google Drive with a real export, retry and idempotency check.
11. Re-run Supabase Storage/B2/provider/RAG evidence on the final revision where required.
12. Run controlled 9-category / 170-file Book Intelligence acceptance.
13. Run authenticated Playwright production smoke.
14. Complete WCAG keyboard/screen-reader/responsive checks.
15. Capture Lighthouse/performance baseline.
16. Verify Sentry live ingestion.
17. Run mobile EAS/device smoke.
18. Run GDPR owner-data export/delete and cleanup verification.
19. Complete final production smoke on the exact release revision.
20. Obtain release approval and tag only after all required gates are green.
21. Only then activate Phases 13–21 one controlled phase at a time with evidence.

## Explicitly deferred / optional

- Paid LLM activation.
- Google Drive re-authorization/account-owner consent if required by the final OAuth flow.
- Cloudflare Workers/Pages/R2 production adoption; no active Cloudflare production resource is currently evidenced.
- Vercel adoption; no current repository/account evidence establishes Vercel as an active target.
- R2 production adoption unless explicitly provisioned and justified.
- Upstash Redis/QStash expansion.
- PostHog, Doppler/Infisical, k6/Artillery, Better Stack, Mintlify/Docusaurus and dedicated search/vector infrastructure.

## Source-of-truth rules

- `CURRENT_STATE.md` owns current evidence, blockers and next actions.
- `ROADMAP.md` owns strategic phases, acceptance, deferred scope and backlog.
- `PROJECT_OVERVIEW.md` owns product/architecture boundaries.
- `docs/DEPLOYMENT.md` owns deployment configuration and release procedure.
- `docs/STORAGE.md` owns provider roles and storage routing.
- Historical documents under `archive/legacy/` are not current operational truth.
- A configured service, code contract, test result or deployment artifact is not production PASS by itself; release PASS requires observed evidence for the final revision/configuration.
- Never record secret values.
