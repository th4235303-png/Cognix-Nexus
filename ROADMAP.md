# Cognix Nexus — Strategic Roadmap

## Latest roadmap status — 2026-10-13 (supersedes older P0 status below)

- Provider E2E now passes in [run #38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584), including Google Drive, Supabase Storage, B2, Cloudinary, extraction, Cohere 1536 embeddings, RRF/RAG/citation, tiered storage and owner isolation.
- Google Drive's prior HTTP 404 blocker is resolved for that run. Optional Gemini 401, Hugging Face 400, Groq 429 and Cloudflare 410 remain route-specific diagnostics.
- Sentry, recovery, Book contract and browser smoke were skipped and remain pending. Render direct health/readiness, live env inventory, mobile, accessibility, performance, GDPR and grouped manual verification also remain open.
- PR #39 safety guardrails passed standard CI on merge revision `54abdf355ceacc879c4842d0992e08ec61f584a8`: frontend/backend/mobile CI, CodeQL, Book synthetic acceptance contract and the ephemeral-container restore drill passed. This does not substitute for the real production recovery gate.
- Follow-up preflight correction scopes the Book-only gate to `COGNIX_BOOK_ACCEPTANCE_DATABASE_URL` without requiring production `DATABASE_URL`; CI is pending for this latest change. PR remains open and unmerged.
- Next order: confirm latest preflight CI; configure/run the release workflow for authenticated browser smoke and Sentry; verify Render health/readiness and runtime evidence; verify isolated recovery target and cleanup before any real recovery run; finish device/accessibility/performance/GDPR/manual checks; final smoke and release approval.


> Owner: Product/engineering roadmap
> Update when: phase scope, priority, acceptance, deferral, blocker, or backlog changes
> Last Updated: 2026-10-13
> Do NOT put here: live evidence details or step-by-step operational runbooks.

## Completed Phases
- Research foundation and human-review lifecycle.
- Brain Vault/Level Up foundation and Book Intelligence Phase 1–12 implementation foundations.
- Durable processing, evidence lineage, owner isolation, RRF retrieval, export and security foundations.

## Active Phase
### P0 engineering verification
- Latest main CI [38225351392](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38225351392) and CodeQL [38225351317](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38225351317) both PASS on merge commit `c711aa225e7306d1b8b637e241abc05116167b01` (2026-10-12).
- Render API deploy `dep-db69rg0u01pc73fcqm5g` and Worker deploy `dep-db69rg0u01pc73fcqmu0` succeeded and are live on `c711aa2`.
- Render service runtime/root/build/start/health-check/auto-deploy metadata matches the checked-in blueprint. Direct HTTP health/readiness responses and live env-name inventory remain unavailable via the connected tools; no variable was deleted or overwritten.

- Supabase migration 033 is live; targeted RLS initplan and `knowledge_items.chapter_id` index advisor findings are resolved. Supabase Auth leaked-password protection remains disabled because the current Free plan does not permit enabling it (owner-confirmed); treat as a documented plan limitation.
- Release Gates run [#38231060560](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38231060560): preflight PASS, provider E2E FAIL only at Google Drive with `GoogleDriveFolderNotFoundOrInaccessible:HTTP_404`. Storage/RAG/citation/owner-isolation/embedding checks passed; optional Gemini 401, Hugging Face 400, Cloudflare 410 are diagnostic. Next: verify the Actions `GOOGLE_DRIVE_ROOT_FOLDER_ID` and folder access for the OAuth account, then rerun the provider gate. Earlier run #38046919712 remains historical evidence.

### P1 UI completion/polish
- UI foundation/state normalization.
- Core Brain Vault and research workflows.
- RAG/evidence/review UI.
- Level Up/Vizora/export polish.
- Responsive/accessibility work.

### Production smoke and release approval
- Final production smoke.
- Release approval/tag after all external gates are green.

### Current execution order
1. Close the remaining real-world release gates that are executable now: provider/storage drills, authenticated browser smoke, accessibility/performance, recovery, GDPR and observability.
2. Complete the controlled Book Intelligence acceptance corpus and lifecycle/E2E work listed below.
3. Complete P1 UI normalization, core workflows, evidence/review states, responsive/accessibility verification and mobile/device checks.
4. Re-run the full production smoke against the intended main revision.
5. Approve and tag the release only after all required gates are green.
6. Then activate the Phase 13+ implementation slices only after the release is green; non-runtime foundations may be prepared in parallel but never substitute for release gates.

The 2026-10-08 close-out verified the migration head, worker policy, Secret Vault KDF and R2 role at that time. As of 2026-10-12, the live Worker auto-deploy trigger reports `commit`, matching the checked-in blueprint.

## Pending Verification / Acceptance
- Direct Render API `/health` and `/ready`, post-deploy worker health/runtime logs, and safe live environment-variable inventory (blueprint names are known, live names cannot be enumerated by the connected tool).
- Supabase Auth leaked-password protection is unavailable on the current Free plan (owner-confirmed); retain as an explicit security limitation and revisit only if the plan/settings support it.
- Repeat real AI provider E2E after reconciling provider access/model/quota configuration; prior run had six probe failures.
- Google Drive provider E2E runs #38231060560 and #38259902309 both return `GoogleDriveFolderNotFoundOrInaccessible:HTTP_404`, while owner confirms Actions root-folder ID and refresh token were checked repeatedly. Code review identified a likely scope mismatch: OAuth requests `drive.file` but the workflow targets an existing owner-provided root folder. Proposed branch `fix/google-drive-root-folder-scope` requests full Drive scope; because this is broader sensitive access, owner must review and re-authorize only after the change is accepted. Do not mark this resolved until a real export and retry/idempotency pass.
- Supabase Storage and Backblaze B2 >50 MB drills previously passed in provider E2E #38046919712; repeat if fresh release evidence is required.
- Authenticated Playwright production smoke.
- Mobile EAS/device smoke.
- WCAG keyboard/screen-reader/responsive sweep.
- Lighthouse/performance run.
- Backup/restore/rollback drill.
- GDPR export/delete.
- Sentry live ingestion.

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

**Foundation prepared:** provider-agnostic `EvidenceRef`, `Finding`, `AgentRun`, and `DecisionRecord` contracts plus evidence/review invariants are present in `web-platform/backend/app/services/active_layer/` and `docs/PHASE_13_FOUNDATION.md`.

**Activation order after release:** persistence/events → lease/heartbeat reuse → evidence validation → provider adapter boundary → evaluation fixtures → runtime orchestration.

### Phase 14 — Learning Science
Decay, interleaving, learning paths, knowledge gaps and deep research.

### Phase 15 — Life Integration
Timeline, local-only mood, user-triggered ambient, context restoration and encrypted capsules.

### Phase 16 — Advanced Layer
Private wiki, growth metrics, evidence-backed ideas, offline/local-model boundary and encrypted legacy handoff.

**Master Plan additions reconciled:** Secret Vault advanced features are Phase 16 scope: TOTP generation, SSH-key storage, breach checking via privacy-preserving k-anonymity, emergency kit generation, and encrypted export/import. These are implementation scope, not current production claims.

### Phase 17 — Cognix Core Integration
Source inbox expansion, claim review, translation versioning, fact-check workflow, research reports and export integration.

**Master Plan additions reconciled:** Document Assistant detail is Phase 17 scope: document-type classification (contract/letter/form/invoice/receipt/meeting note/study material/medical report/legal notice/business card), OCR review UI, low-confidence highlighting, medical/legal disclaimers, and Inbox → Processing → Review → Approved → Indexed → Archived → Deleted lifecycle.

**Language Tutor detail is Phase 17 scope:** MM↔JP/KR reading/vocabulary/translation, parallel text, grammar explanations/examples, JP furigana/romaji and KR romanization support, TTS, writing correction, role-play conversations, grammar/vocabulary/translation quizzes, and CEFR/JLPT/TOPIK mapping.

### Phase 18 — Vizora Lens
Batch media, richer OCR/vision, metadata, review, media links and Drive package.

**Master Plan additions reconciled:** batch upload, diagram/chart/infographic analysis, EXIF/document metadata extraction, human review, media↔notes/concepts links, and Drive package export containing original + OCR text + metadata JSON + thumbnail.

### Phase 19 — Native/Product UX
Offline-first reader, share-sheet/capture, camera OCR, voice, push, biometric boundary, JP/KR, accessibility and responsive polish.

**Master Plan additions reconciled:** full native offline reading, iOS/Android share-sheet capture, camera OCR, voice-note capture, review/digest push notifications, biometric Vault unlock, JP/KR native UI, and WCAG AA/keyboard/screen-reader/responsive polish.

### Phase 20 — Production Engineering
Durable leases, backup/restore, migrations, observability, evaluation datasets, E2E, stress, security and rollback.

**Evaluation scope:** AI grounding/hallucination/JSON, agent finding/synthesis quality, learning decay/path effectiveness, latency/storage/quota benchmarks, and prompt-injection/RLS/SSRF security suites.

### Phase 21 — Release
Re-enable frontend deployment, configure domains/TLS/secrets, smoke-test and tag release.

## Deferred
- Paid LLM activation.
- Google Drive re-authorization/account-owner consent.
Google Drive re-authorization is a current external acceptance blocker; paid LLM activation remains deferred.

## Blocked
- Final production smoke.
- Final release/tag.
Block condition: required external/provider/browser/device/recovery gates remain unresolved.

## Master Plan reconciliation / newly tracked scope
The following items from the supplied Master Plan v4.0 are now explicitly tracked above rather than treated as “missing from the roadmap”: Document Assistant detail, Language Tutor detail, Secret Vault advanced features, Phase 13–16 feature-level scope, Vizora Lens detail, Native/Product UX detail, evaluation datasets, and documentation coverage.

These items are intentionally **not marked complete**. Existing Phase 13–21 contracts/foundations count only as preparation. Runtime activation remains behind the release gate invariant.

### Documentation coverage
Canonical documentation now includes `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/PIPELINE.md`, `docs/PROMPTS.md`, `docs/TROUBLESHOOTING.md`, `docs/CHANGELOG.md`, `docs/USER_GUIDE.md`, and `docs/AGENT.md`. Existing docs are authoritative; duplicated legacy docs should not be created.

### Evaluation datasets
Evaluation fixture work is Phase 20 scope and may be prepared in parallel. It must remain deterministic, owner/evidence aware, and separate from production PASS evidence.

## Backlog / Optional
- R2 as a production provider only if scale/requirements justify it and live configuration verifies it.
- Upstash Redis/QStash expansion.
- PostHog.
- Doppler/Infisical.
- k6/Artillery.
- Better Stack.
- Mintlify/Docusaurus.
- Cloudflare WAF after a Cognix domain/zone exists.
- Dedicated vector database.
- Dedicated search engine.
- Workflow orchestration infrastructure.

## Future-phase preparation map
Detailed non-runtime preparation boundaries and activation batches are tracked in `docs/FUTURE_PHASE_FOUNDATIONS.md`.

## Non-negotiable principles
1. AI output is not canonical without required review.
2. Answers retain evidence/citation lineage.
3. Durable data does not silently fall back to memory.
4. Jobs are idempotent and recoverable.
5. Optional providers fail closed.
6. Security/ownership boundaries are enforced before release.
7. Releases land on main and pass CI.

## Source of truth
CURRENT_STATE.md owns current actions/evidence. This file owns strategic phases, acceptance, future/deferred/blocked/backlog scope. Historical roadmap sources are archived under archive/legacy/.
