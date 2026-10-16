# Current verification update — 2026-10-16

This section supersedes conflicting historical status below. Use the GitHub `main` branch head for the current revision.

- Repository structure and dependency/test fixes are committed to `main`.
- Production CI run [#38882163315](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38882163315) passed on revision `a57c804087d725d6b7ce99f988892f245c87fb3d`: frontend build, backend lint/compile/tests/migration pre-flight, live API `/health` + `/ready`, and live frontend HTTPS/HTML smoke all passed. Cognix Core CI [#38882163328](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38882163328) and CodeQL [#38882163206](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38882163206) also passed.
- Migration `044_restrict_service_managed_brain_soul_youtube.sql` is applied. The application migration registry in `public.cognix_schema_migrations` confirms migrations through `044`; this is distinct from the separate Supabase CLI migration history, which still reports `033`.
- Migration 044 removes `anon` and `authenticated` table and sequence privileges from `brain_soul_context`, `brain_soul_syntheses`, `youtube_channels`, and `brain_youtube_videos`, and revokes those grants by default for future public tables/sequences.
- Production database verification shows the expected public schema is present and all current public tables have RLS enabled. User-facing tables have policies; the four service-managed Brain Soul/YouTube tables intentionally have no frontend policies and no `anon`/`authenticated` Data API privileges.
- Render API deploy `dep-db8u9ubrjlhs73dirt80` and Worker deploy `dep-db8uarqvcj2c73b8hkgg` are live. Frontend deploy `dep-db8v1sgts6fs73dptmeg` for revision `a57c804087d725d6b7ce99f988892f245c87fb3d` is live.
- Supabase Auth leaked-password protection is **explicitly deferred/accepted for the current free-tier setup** and is no longer a release blocker in this project state. Do not keep repeating it as a required task unless the plan changes.
- Remaining release work is now limited to production evidence and external acceptance gates listed below.

## Repository

- Canonical active application paths are `apps/web-platform/frontend` and `apps/web-platform/backend`.
- `apps/mobile` is the reserved mobile product surface.
- `archive/legacy` is historical/reference material and is not active runtime code.
- `docs/REPOSITORY_STRUCTURE.md` documents the canonical layout; the repository Git tree is the authoritative path inventory.

## Render

- Connected workspace: `Cognix Core`.
- API: `https://cognix-core-ypak.onrender.com`.
- Worker: `https://cognix-core-worker-runtime.onrender.com`.
- Frontend: `https://cognix-nexus-frontend.onrender.com`.
- API live verification: `/health` returned `status=ok`; `/ready` returned `status=ready`, `database_configured=true`, `database_reachable=true`, `persistence_mode=postgresql`, and `database_required=true`.
- Browser smoke verified HTTPS frontend `/login` and `/forgot-password` routes load. Authenticated actions were not tested because no test-user credentials were available.
- Render dashboard service paths still use legacy aliases (`web-platform/backend` and `cd web-platform/frontend` in the frontend build command) while `render.yaml` documents canonical `apps/web-platform/...` paths. Current services are live through the compatibility symlink; migrate service settings to canonical paths when the connected Render control surface permits it.

## Supabase

- Production project: `Cognix-Core` (`jarfusheiqkfcbeljvhj`), region `ap-southeast-1`, status `ACTIVE_HEALTHY`.
- Production public schema contains the current application tables, including Brain Soul and YouTube tracker tables.
- All current public tables have RLS enabled.
- Migration 044 is applied and recorded in `public.cognix_schema_migrations`.
- `anon` and `authenticated` have no table/sequence privileges on the four service-managed Brain Soul/YouTube tables.
- The four service-managed tables intentionally have zero frontend RLS policies because they are backend/service-role-only.
- Supabase CLI migration history remains at historical head 033; the application migration registry is the backend migration ledger through 044.
- Leaked-password protection is intentionally skipped/accepted under the current free-tier constraint and is not an actionable blocker.

## Remaining work — required before release

1. Complete a real production backup → isolated restore → rollback drill; CI's isolated drill is not a substitute.
2. Reconcile live environment-variable **names** against code, `render.yaml`, CI, recovery and test workflows without exposing secret values; the connected Render integration cannot enumerate live variable names.
3. Confirm Supabase public frontend configuration and auth redirect URLs; Render-hosted HTTPS frontend/API routes have been verified.
4. Decide whether to migrate the Render dashboard service paths from the compatibility bridge to canonical `apps/web-platform/...` paths.
5. Decide whether Vercel/Netlify remain intentionally unused; Render is the currently observed frontend host.
6. Review unused indexes using actual query-plan/usage evidence; delete none automatically.
7. Re-run Cloudinary fresh round-trip evidence if required by release policy.
8. Prove Google Drive with a real export, retry and idempotency check; merged scope change requires fresh account-owner OAuth consent.
9. Re-run Supabase Storage/B2/provider/RAG evidence on the final revision where required.
10. Run controlled 9-category / 170-file Book Intelligence acceptance; CI's synthetic contract is not corpus acceptance.
11. Run authenticated Playwright production smoke with a dedicated test account.
12. Complete WCAG keyboard/screen-reader/responsive checks.
13. Capture Lighthouse/performance baseline.
14. Verify Sentry live ingestion.
15. Run mobile EAS/device smoke; CI config validation is not a device test.
16. Run GDPR owner-data export/delete and cleanup verification.
17. Complete final production smoke on the exact release revision.
18. Obtain release approval and tag only after all required gates are green.
19. Only then activate Phases 13–21 one controlled phase at a time with evidence.

## Explicitly deferred / optional

- Supabase Auth leaked-password protection under the current free-tier constraint.
- Paid LLM activation.
- Google Drive re-authorization/account-owner consent if required by the final OAuth flow.
- Cloudflare Workers/Pages/R2 production adoption.
- Vercel adoption.
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
