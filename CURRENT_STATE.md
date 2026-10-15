# Current verification update — 2026-10-15 07:10 UTC

This update supersedes conflicting historical status below.

- Current main revision: `54be85aa883b589b392d14279ea73e830951a522`.
- Cognix Core CI and CodeQL are green on this revision. Backend CI confirms migration smoke (all 41 registered migrations), unit/integration tests, Book Intelligence synthetic acceptance, backup/isolated restore drill, coverage gate, and dependency audit all passed.
- Render API, worker and frontend deployments for this revision are all LIVE. API logs show repeated `GET /health 200 OK`; worker logs show `worker_started persistence=postgresql database_configured=True`.
- Supabase `public.cognix_schema_migrations` records migrations 034–041 as applied, including `041_phase22_book_acceptance_schema.sql`.
- **Release remains BLOCKED pending final production verification.** A current post-deploy `/ready` response has not yet been captured; safe live environment-variable name reconciliation, public frontend/auth/API smoke, real provider/Google Drive acceptance, controlled 9-category/170-file Book Intelligence acceptance, accessibility/performance/mobile/Sentry/GDPR and final release smoke remain outstanding. Do not activate Phases 13–21 or tag a release before these gates pass.
- Supabase Auth leaked-password protection remains a security WARN pending an explicit enable/exception decision. INFO-level unused indexes must be reviewed, not automatically deleted.
- Live service URLs: frontend https://cognix-nexus-frontend.onrender.com ; worker https://cognix-core-worker-runtime.onrender.com. The API public URL should be taken from Render service configuration rather than guessed.

---

# Cognix Nexus — Current State

## Latest verified audit — 2026-10-15

This section supersedes older live-status statements below where they conflict. Historical evidence remains useful only when explicitly labelled historical.

### Repository

- Latest main commit observed after this audit: `40558ee3f6bed1c1d2dde79c80942754a6353534` (`fix(auth): restore current owner dependency for media and release routers`).
- The latest fix restores `get_current_owner_id()` in `app.auth`, matching the existing Phase 18/19 media router and Phase 20/21 release-evidence router imports that caused the latest API startup failure.
- Phase 13–21 runtime implementation is present in the repository. The latest documented implementation set reports 243/243 local deterministic tests across Ph13–21, but production activation remains gated.
- No `vercel.json` exists and repository search found no Vercel references. Vercel is therefore **not verified as a deployment target**.

### Render

- Connected workspace: `Cognix Core`.
- Live services: `Cognix-Core` API, `cognix-core-worker-runtime`, and `cognix-nexus-frontend`.
- API service configuration: Python, `web-platform/backend`, `pip install -r requirements.lock`, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, `/health`, auto-deploy on commit, Singapore region.
- Worker configuration: Python, `web-platform/backend`, same locked build, `python -m app.worker`, `/health`, auto-deploy on commit, Singapore region.
- Frontend configuration: Node, repository root, build `cd web-platform/frontend && npm ci && npm run build`, start `cd web-platform/frontend && npm start`, Singapore region.
- Worker deploy for commit `5067c12b3235a87b2881f320350706b54ee0b5a2` is **LIVE**.
- The matching API deploy failed after a successful build because `media_boundary.py` and `release_evidence.py` imported `get_current_owner_id`, which was absent from `app.auth`. The failure is now fixed in main commit `40558ee3...`; a new Render API deploy still needs to be observed before marking the runtime healthy.
- Render currently hosts the frontend as well. This supersedes the older documentation assumption that Netlify was the active frontend host.
- Live environment-variable enumeration is not available through the connected Render action surface; do not claim blueprint/live env parity until an inventory is captured.

### Supabase

- Production project: `Cognix-Core` (`jarfusheiqkfcbeljvhj`), region `ap-southeast-1`, status `ACTIVE_HEALTHY`, PostgreSQL 17.11.
- Live migration head: `033_rls_policy_initplan_indexes` (`20261012034910`).
- Security advisor: one WARN remains — Supabase Auth leaked-password protection is disabled.
- Performance advisor: INFO-level unused-index findings remain (69 at audit time). No critical performance lint was reported by the connected advisor.
- Restore-drill project `Cognix-Core-restore-drill` is also `ACTIVE_HEALTHY`.
- Do not remove the unused indexes automatically. Review query plans/usage and remove only after confirming they are genuinely unnecessary.

### Cloudflare

- One Cloudflare account is connected.
- Current account audit returned **0 zones, 0 Workers scripts, and 0 Pages projects**.
- R2 is not enabled; the Cloudflare API explicitly reports that R2 must first be enabled in the dashboard.
- Therefore Cloudflare is currently **not an active production dependency** for the Cognix deployment path. Existing backend R2/Cloudflare adapter code remains compatibility/optional infrastructure until a real zone or service is provisioned.

### Other providers / release gates

- Cloudinary integration exists in the application, but a fresh asset round-trip was not re-run during this audit because the available Cloudinary list surface returned incompatible metadata-schema responses. Do not convert older evidence into a fresh 2026-10-15 PASS.
- Google Drive export remains an external acceptance gate and must be proven with a real export plus retry/idempotency verification on the intended OAuth account/folder.
- Supabase Storage/B2/provider/RAG checks have historical passing evidence, but release policy requires fresh evidence when the final revision/configuration changes.

## 1. Release status

**BLOCKED — pre-final-production-verification.**

The immediate Render API startup defect has been identified and patched, but the patch has not yet been deployed and re-verified. Final smoke, tagging and Phase 13–21 production activation remain blocked until the full release gate is green.

## 2. Completed / code-ready

- Research foundation and human-review lifecycle.
- Brain Vault and Book Intelligence foundations through Phase 1–12.
- Durable processing, evidence lineage, owner isolation, RRF retrieval and export foundations.
- Phase 13–21 runtime implementation and deterministic test contracts are present in the repository.
- Supabase migration 033 is live and targeted RLS/initplan/index findings from the earlier audit are resolved.
- Render API, worker and frontend services exist with commit-triggered deployment.
- Provider-key-only AI routing and fixed 1536-dimension production embedding compatibility are implemented.
- Latest API startup defect caused by a missing `get_current_owner_id` auth dependency is patched in main.

## 3. Remaining work — required before release

### A. Deploy and verify the Render API fix first

1. Let Render build/deploy main commit `40558ee3f6bed1c1d2dde79c80942754a6353534`.
2. Confirm the API starts without import errors.
3. Capture `/health` and `/ready` external evidence from the intended public API.
4. Confirm worker health/logs after the matching API revision is live.
5. Capture a safe live environment-variable **name** inventory and reconcile it with code, `render.yaml`, CI, recovery and test workflows. Never print secret values.

### B. Frontend hosting reconciliation

6. Treat Render `cognix-nexus-frontend` as the current frontend host unless the owner intentionally chooses another platform.
7. Verify production domain, TLS, public API URL, Supabase public configuration and auth redirect URLs on the actual frontend host.
8. If Vercel is intended instead, create/confirm the Vercel project and migrate the deployment configuration deliberately; no current repository/account evidence establishes Vercel today.
9. Remove or archive stale Netlify-only deployment instructions only after confirming no operational dependency remains.

### C. Supabase

10. Keep migration head 033 as the current production baseline unless a reviewed migration is intentionally promoted.
11. Decide whether to enable leaked-password protection. The current advisor still reports it disabled; if the current plan/settings cannot enable it, document the limitation rather than claiming PASS.
12. Review the 69 INFO unused-index findings; remove none automatically.
13. Run a fresh database readiness/advisor capture after any schema change.
14. Complete the isolated restore/rollback drill against the dedicated restore target and record cleanup.

### D. Provider acceptance

15. Re-run provider/storage acceptance on the intended release revision.
16. Prove Google Drive with a real export, retry and idempotency check using the correct OAuth account and root folder.
17. Re-run Cloudinary write/read/checksum evidence if release policy requires fresh proof.
18. Re-run Supabase Storage and B2 write/read/checksum evidence if the final release revision changed the relevant code/configuration.
19. Verify Cohere 1536-dimension embedding production compatibility and RAG/citation behavior on the final revision.

### E. Product/release gates

20. Run controlled Book Intelligence acceptance: 9 categories / 170-file corpus, duplicate fingerprint, checkpoint/resume, durable ledger, distillation, lesson packs, derived-book lineage and export.
21. Run authenticated Playwright production smoke across the intended pages and critical flows.
22. Complete WCAG keyboard, screen-reader, responsive and accessibility verification.
23. Capture Lighthouse/performance baseline and investigate regressions.
24. Run Sentry live ingestion verification.
25. Run mobile EAS/device smoke.
26. Run GDPR owner-data export/delete and cleanup verification.
27. Run production backup → isolated restore → rollback drill.
28. Complete grouped manual verification last.
29. Run final production smoke against the exact release revision.
30. Obtain release approval and tag only after all required gates are green.

### F. Phase 13–21 activation

31. Do **not** activate Phase 13–21 production runtime merely because the code exists.
32. After release approval, activate Phase 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 one controlled phase at a time, with its own evidence.

## 4. Explicitly deferred / optional

- Paid LLM activation.
- Google Drive re-authorization/account-owner consent if required by the final OAuth flow.
- Cloudflare Workers/Pages/R2 production adoption; currently no active Cloudflare resource is present.
- Vercel adoption; currently no repository or connected-account evidence.
- R2 as a production storage provider unless scale/requirements justify it and the resource is explicitly provisioned.
- Upstash Redis/QStash expansion.
- PostHog, Doppler/Infisical, k6/Artillery, Better Stack, Mintlify/Docusaurus and dedicated search/vector infrastructure.

## 5. Source-of-truth rules

- `CURRENT_STATE.md` owns current evidence, blockers and next actions.
- `ROADMAP.md` owns strategic phases, acceptance, deferred scope and backlog.
- `PROJECT_OVERVIEW.md` owns product/architecture boundaries.
- `docs/DEPLOYMENT.md` owns deployment configuration and release procedure.
- `docs/STORAGE.md` owns provider roles and storage routing.
- Historical documents under `archive/legacy/` are not current operational truth.
- Static code, configured secrets, prepared contracts or a live deployment are not production PASS by themselves.
- Record only observed results, including revision/time/cleanup status; never record secret values.
