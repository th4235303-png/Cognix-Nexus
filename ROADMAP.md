# Cognix Nexus — Strategic Roadmap

> Owner: Product/engineering roadmap
> Update when: phase scope, priority, acceptance, deferral, blocker, or backlog changes
> Last Updated: 2026-10-08
> Do NOT put here: live evidence details or step-by-step operational runbooks.

## Completed Phases
- Research foundation and human-review lifecycle.
- Brain Vault/Level Up foundation and Book Intelligence Phase 1–12 implementation foundations.
- Durable processing, evidence lineage, owner isolation, RRF retrieval, export and security foundations.

## Active Phase
### P0 engineering verification
- Engineering verification.
- Storage/processing verification.
- Security regression.

### P1 UI completion/polish
- UI foundation/state normalization.
- Core Brain Vault and research workflows.
- RAG/evidence/review UI.
- Level Up/Vizora/export polish.
- Responsive/accessibility work.

### Production smoke and release approval
- Final production smoke.
- Release approval/tag after all external gates are green.

## Pending Verification / Acceptance
- Real AI provider E2E.
- Google Drive OAuth/account drill.
- Supabase Storage drill.
- Backblaze B2 drill.
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

### Phase 14 — Learning Science
Decay, interleaving, learning paths, knowledge gaps and deep research.

### Phase 15 — Life Integration
Timeline, local-only mood, user-triggered ambient, context restoration and encrypted capsules.

### Phase 16 — Advanced Layer
Private wiki, growth metrics, evidence-backed ideas, offline/local-model boundary and encrypted legacy handoff.

### Phase 17 — Cognix Core Integration
Source inbox expansion, claim review, translation versioning, fact-check workflow, research reports and export integration.

### Phase 18 — Vizora Lens
Batch media, richer OCR/vision, metadata, review, media links and Drive package.

### Phase 19 — Native/Product UX
Offline-first reader, share-sheet/capture, camera OCR, voice, push, biometric boundary, JP/KR, accessibility and responsive polish.

### Phase 20 — Production Engineering
Durable leases, backup/restore, migrations, observability, evaluation datasets, E2E, stress, security and rollback.

### Phase 21 — Release
Re-enable frontend deployment, configure domains/TLS/secrets, smoke-test and tag release.

## Deferred
- Paid LLM activation.
- Google Drive re-authorization/account-owner consent.
These are not current P0 blockers.

## Blocked
- Final production smoke.
- Final release/tag.
Block condition: required external/provider/browser/device/recovery gates remain unresolved.

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
