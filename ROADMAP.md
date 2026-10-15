# Cognix Nexus — Strategic Roadmap

## Latest roadmap status — 2026-10-15

- **Phase 13–21 runtime implementation: COMPLETE in code** — the repository contains the implementation set and deterministic tests, but production activation remains blocked by the release gate invariant.
- **Immediate Render fix identified:** the latest API deploy failed because Phase 18/19 and Phase 20/21 routers imported `get_current_owner_id` while `app.auth` did not define it. Main commit `40558ee3f6bed1c1d2dde79c80942754a6353534` restores that dependency. The fix still needs a successful Render deployment and health/readiness evidence.
- **Infrastructure reconciliation:** Render is currently the actual hosting platform for the frontend, API and worker. The worker is live on the previous `5067c12b...` revision; the matching API revision failed and is being repaired.
- **Supabase:** production project is healthy and migration head is 033. One security WARN remains for disabled leaked-password protection; performance advisor findings are INFO-level unused indexes.
- **Cloudflare:** account is connected but no zones, Workers scripts or Pages projects are currently present; R2 is not enabled. Cloudflare is not a current production dependency.
- **Vercel:** no repository configuration or connected deployment evidence was found. Vercel is not currently part of the verified architecture.
- **Netlify:** retained as legacy documentation only unless a live dependency is rediscovered.

## Current execution order

1. Deploy the `40558ee3` auth fix to Render and prove API `/health` + `/ready`.
2. Verify worker health and safe live environment-variable names against `render.yaml` and CI.
3. Reconcile the actual frontend deployment/domain/auth configuration on Render; choose Vercel only if intentionally adopted.
4. Capture fresh Supabase readiness/security evidence and decide how to handle leaked-password protection.
5. Re-run provider/storage acceptance, including real Google Drive export + retry/idempotency.
6. Run Book Intelligence acceptance corpus and lifecycle checks.
7. Run authenticated browser, accessibility, performance, Sentry, mobile, GDPR and recovery gates.
8. Complete grouped manual verification last.
9. Run final production smoke on the exact release revision.
10. Approve and tag the release.
11. Only then activate Phase 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21 one phase at a time.

## Completed Phases

- Research foundation and human-review lifecycle.
- Brain Vault/Level Up foundation and Book Intelligence Phase 1–12 implementation foundations.
- Durable processing, evidence lineage, owner isolation, RRF retrieval, export and security foundations.
- Phase 13–21 runtime implementation in the repository, including release-evidence/readiness contracts.

## Active Phase

### P0 — Production verification and infrastructure reconciliation

The project is code-complete enough to enter final verification, but it is not release-complete. A successful build or a live worker does not compensate for a failed API deployment or missing external acceptance evidence.

### P1 — UI completion/polish

- UI state normalization.
- Core Brain Vault and research workflows.
- RAG/evidence/review UI.
- Level Up/Vizora/export polish.
- Responsive/accessibility work.
- Mobile/device verification.

### Production smoke and release approval

- Final production smoke.
- Release approval/tag after all required external gates are green.

## Pending Verification / Acceptance

- Deploy and verify the Render API auth fix.
- Render API `/health` and `/ready` plus worker health/runtime verification on the final matching revision.
- Safe live environment-variable name inventory and blueprint reconciliation.
- Frontend production domain/TLS/API/Auth redirect verification on the current Render frontend.
- Supabase Auth leaked-password protection decision/verification.
- Review of 69 INFO-level unused-index findings; no automatic deletion.
- Real Google Drive export, retry and idempotency verification.
- Fresh provider/storage checks on the final release revision.
- Controlled 9-category / 170-file Book Intelligence acceptance.
- Authenticated Playwright production smoke.
- Mobile EAS/device smoke.
- WCAG keyboard/screen-reader/responsive sweep.
- Lighthouse/performance baseline.
- Backup/restore/rollback drill.
- GDPR export/delete.
- Sentry live ingestion.
- Grouped manual verification.
- Final production smoke and release approval.

## Book Intelligence

- Controlled 9-category / 170-file dry-run.
- Book lifecycle state normalization.
- AI Reading Room provider-backed E2E.
- Duplicate fingerprint E2E.
- Durable reading ledger.
- Book-level knowledge distillation.
- Category lesson packs.
- Derived books.
- Markdown/plain-text reading ledger export.

Acceptance: exact duplicate auto-stop; checkpoint/resume; partial results while processing; durable progress history; source-linked distillation; provenance-preserving cross-book synthesis; derived-book source manifests; UI/worker/database lifecycle consistency.

## Future Phases

### Phase 13 — AI Active Layer
Agent lifecycle, durable execution, evidence-bound findings, synthesis, decision support, writing and Feynman.

### Phase 14 — Learning Science
Decay, interleaving, learning paths, knowledge gaps and deep research.

### Phase 15 — Life Integration
Timeline, local-only mood, user-triggered ambient, context restoration and encrypted capsules.

### Phase 16 — Advanced Layer
Private wiki, growth metrics, evidence-backed ideas, offline/local-model boundary and encrypted legacy handoff.

Secret Vault advanced features remain Phase 16 scope: TOTP generation, SSH-key storage, breach checking via privacy-preserving k-anonymity, emergency kit generation, and encrypted export/import.

### Phase 17 — Cognix Core Integration
Source inbox expansion, claim review, translation versioning, fact-check workflow, research reports and export integration.

Document Assistant and Language Tutor remain Phase 17 scope.

### Phase 18 — Vizora Lens
Batch media, richer OCR/vision, metadata, review, media links and Drive package.

### Phase 19 — Native/Product UX
Offline-first reader, share-sheet/capture, camera OCR, voice, push, biometric boundary, JP/KR, accessibility and responsive polish.

### Phase 20 — Production Engineering
Durable leases, backup/restore, migrations, observability, evaluation datasets, E2E, stress, security and rollback.

### Phase 21 — Release
Production verification, domains/TLS/secrets, smoke-test, release approval and tagging. The implementation foundation exists, but the current release gate must still be cleared.

## Deferred / Optional

- Paid LLM activation.
- Google Drive re-authorization/account-owner consent if required.
- Cloudflare Workers/Pages/R2 adoption.
- Vercel adoption.
- R2 as a production provider only if scale/requirements justify it.
- Upstash Redis/QStash expansion.
- PostHog.
- Doppler/Infisical.
- k6/Artillery.
- Better Stack.
- Mintlify/Docusaurus.
- Dedicated vector database.
- Dedicated search engine.
- Workflow orchestration infrastructure.

## Documentation coverage

Canonical documentation includes `PROJECT_OVERVIEW.md`, `CURRENT_STATE.md`, `ROADMAP.md`, `TOOL.md`, `SECURITY.md`, `UI_DESIGN_SYSTEM.md`, and the detailed documents under `docs/`. Historical source material remains under `archive/legacy/` and is not current operational truth.

## Non-negotiable principles

1. AI output is not canonical without required review.
2. Answers retain evidence/citation lineage.
3. Durable data does not silently fall back to memory.
4. Jobs are idempotent and recoverable.
5. Optional providers fail closed.
6. Security/ownership boundaries are enforced before release.
7. Releases land on main and pass CI.
8. Production PASS requires observed evidence on the intended revision; configuration or code readiness alone is insufficient.

## Source of truth

`CURRENT_STATE.md` owns current actions/evidence. This file owns strategic phases, acceptance, future/deferred/blocked/backlog scope. Historical roadmap sources are archived under `archive/legacy/`.
