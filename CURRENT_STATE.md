# Current verification update — 2026-10-16

This update supersedes conflicting historical status below.

- Current `main` revision: `19954526b251fd407618aef84c3d03493af7a903`.
- Branch cleanup is complete: only `main` remains; stale Dependabot branches/PRs were merged when safe and closed when not safe to merge.
- Safe dependency updates now on `main` include Pillow 12.3.0, PyJWT 2.15.1, python-json-logger 4.2.0 and psycopg 3.3.6.
- Next.js 16 and the remaining stale Radix/cmdk/uvicorn Dependabot updates were intentionally closed rather than force-merged. They can be reconsidered as fresh updates against current `main` when deliberately tested.
- A repository compatibility symlink `web-platform -> apps/web-platform` was added because the connected Render services still have legacy `web-platform/...` paths configured. This is a compatibility bridge, not the canonical source layout.
- Render services currently use legacy root/build paths (`web-platform/backend` and `web-platform/frontend`) while the repository's canonical paths are `apps/web-platform/backend` and `apps/web-platform/frontend`. The compatibility symlink is intended to unblock the existing services; the Render service configuration should still be migrated to the canonical paths when the connected Render control surface permits it.
- Render API, worker and frontend deployments for the previous known-good revision were live, but the API deployment for the reorganized revision failed before the compatibility bridge was added. A fresh post-change deployment must be observed before marking production healthy.
- Release remains **BLOCKED pending final production verification**. `/ready`, safe live environment-variable-name reconciliation, public frontend/auth/API smoke, real provider/Google Drive acceptance, controlled 9-category/170-file Book Intelligence acceptance, accessibility/performance/mobile/Sentry/GDPR and final release smoke remain outstanding.
- Supabase Auth leaked-password protection remains a security WARN pending an explicit enable/exception decision. INFO-level unused indexes must be reviewed, not automatically deleted.

## Repository

- Canonical active application paths are `apps/web-platform/frontend` and `apps/web-platform/backend`.
- `apps/mobile` is the reserved mobile product surface.
- `archive/legacy` is historical/reference material and is not active runtime code.
- `docs/REPOSITORY_STRUCTURE.md` documents the canonical layout; the repository Git tree is the authoritative path inventory.

## Render

- Connected workspace: `Cognix Core`.
- Live services: `Cognix-Core`, `cognix-core-worker-runtime`, and `cognix-nexus-frontend`.
- API URL: `https://cognix-core-ypak.onrender.com`.
- Frontend URL: `https://cognix-nexus-frontend.onrender.com`.
- Worker URL: `https://cognix-core-worker-runtime.onrender.com`.
- All three services auto-deploy from `main`.
- The connected Render service configuration still reports legacy paths. The repository compatibility symlink was added so those paths resolve to the canonical `apps/web-platform` tree.
- Do not call production PASS until a new deploy from revision `19954526b251fd407618aef84c3d03493af7a903` is observed and `/health` + `/ready` are externally verified.

## Supabase

- Production project: `Cognix-Core` (`jarfusheiqkfcbeljvhj`), region `ap-southeast-1`, status `ACTIVE_HEALTHY`.
- Migration 033 was the previously verified production baseline; repository migrations now extend through 043, so production migration promotion must be deliberate and evidence-backed.
- Security advisor: leaked-password protection remains a WARN.
- Performance advisor: unused-index findings remain informational; no automatic deletion.
- Restore-drill project remains a dedicated verification target.

## Remaining work — required before release

1. Observe a successful Render deploy for the current `main` revision.
2. Capture external `/health` and `/ready` evidence from the intended public API.
3. Confirm worker health/logs on the matching revision.
4. Reconcile live environment-variable **names** against code, `render.yaml`, CI, recovery and test workflows without exposing secret values.
5. Confirm production frontend domain/TLS, API URL, Supabase public configuration and auth redirect URLs.
6. Decide whether to migrate the Render dashboard service paths from the compatibility bridge to the canonical `apps/web-platform/...` paths.
7. Decide whether Vercel/Netlify remain intentionally unused; Render is the currently observed frontend host.
8. Review Supabase leaked-password protection and document PASS/exception.
9. Review unused indexes using actual query-plan/usage evidence; delete none automatically.
10. Complete final backup → isolated restore → rollback evidence.
11. Re-run Cloudinary fresh round-trip evidence if required by release policy.
12. Prove Google Drive with a real export, retry and idempotency check.
13. Re-run Supabase Storage/B2/provider/RAG evidence on the final revision where required.
14. Run controlled 9-category / 170-file Book Intelligence acceptance.
15. Run authenticated Playwright production smoke.
16. Complete WCAG keyboard/screen-reader/responsive checks.
17. Capture Lighthouse/performance baseline.
18. Verify Sentry live ingestion.
19. Run mobile EAS/device smoke.
20. Run GDPR owner-data export/delete and cleanup verification.
21. Complete final production smoke on the exact release revision.
22. Obtain release approval and tag only after all required gates are green.
23. Only then activate Phases 13–21 one controlled phase at a time with evidence.

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
