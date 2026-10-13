# Cognix Nexus — Strategic Roadmap

> Owner: Product/engineering roadmap  
> Update when: phase scope, priority, acceptance, blocker, or deferral changes  
> Last Updated: 2026-10-13  
> Live operational evidence belongs in `CURRENT_STATE.md` and `docs/RELEASE_GATES.md`.

## Completed Foundations

- Research foundation and human-review lifecycle.
- Brain Vault/Level Up foundation and Book Intelligence Phase 1–12 implementation foundations.
- Durable processing, evidence lineage, owner isolation, RRF retrieval, export, and security foundations.
- Provider E2E now has a successful evidence-backed run: [Release Gates #38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584). This closes the previous Google Drive HTTP 404 blocker for that run; it does not close skipped browser, recovery, Book contract, or Sentry gates.

## Active Phase: P0 Engineering Verification

- Provider E2E PASS on 2026-10-13: Supabase Storage, Backblaze B2, Cloudinary, Google Drive, extraction, Cohere 1536-dimensional embeddings, RRF/RAG/citation, tiered storage, and owner isolation passed.
- Optional LLM probes returned Gemini 401, Hugging Face 400, Groq 429, and Cloudflare 410. OpenRouter, Mistral, and Cohere routes succeeded; optional route errors are not the current required-gate blocker.
- Preflight and provider-e2e passed. Sentry, recovery, Book contract, and browser smoke were skipped, so they remain pending.
- Render live health/readiness and live environment-variable inventory remain unverified via the connected tools. No environment variables were deleted or overwritten.
- Supabase migration 033 and targeted RLS/index advisor fixes were verified on 2026-10-12. Supabase Auth leaked-password protection remains disabled due to the owner-reported Free-plan limitation; track as a known security limitation.

## Active Execution Order

1. Book Intelligence acceptance: controlled 9-category / 170-file corpus, duplicate fingerprint/auto-stop, checkpoint/resume, durable ledger, AI Reading Room provider-backed E2E, distillation/lesson packs/derived-book lineage and export.
2. Authenticated Playwright production smoke.
3. Sentry live ingestion probe.
4. Production backup → checksum → isolated restore → rollback/cleanup drill, only with a confirmed isolated target.
5. Render API `/health` and `/ready`, worker health/runtime logs, and safe environment-name inventory.
6. Mobile EAS/device smoke; WCAG keyboard/screen-reader/responsive sweep; Lighthouse/performance baseline; GDPR owner-data export/delete.
7. Complete P1 UI state normalization and grouped manual verification last.
8. Re-run final production smoke on the intended revision; release approval/tag only after required gates are green.
9. Activate Phase 13+ runtime only after release approval; foundations can be prepared in parallel but never substitute for release gates.

## P1 UI Completion / Polish

- UI foundation and state normalization.
- Core Brain Vault and research workflows.
- RAG/evidence/review UI.
- Level Up/Vizora/export polish.
- Responsive and accessibility verification.

## Book Intelligence Acceptance

- Controlled 9-category / 170-file dry-run.
- Book lifecycle state normalization and AI Reading Room provider-backed E2E.
- Duplicate fingerprint E2E and exact-duplicate auto-stop.
- Durable reading ledger, checkpoint/resume, and partial results while processing.
- Book-level knowledge distillation and category lesson packs.
- Derived books with source manifests and provenance-preserving cross-book synthesis.
- Markdown/plain-text reading ledger export.
- Verify UI/worker/database lifecycle consistency and cleanup evidence.

## Future Phases — Planned Scope, Not Current Production Claims

### Phase 13 — AI Active Layer
Agent lifecycle, durable execution, evidence-bound findings, synthesis, decision support, writing, and Feynman. Foundation contracts include `EvidenceRef`, `Finding`, `AgentRun`, and `DecisionRecord`. Activation order after release: persistence/events → lease/heartbeat reuse → evidence validation → provider adapter boundary → evaluation fixtures → runtime orchestration.

### Phase 14 — Learning Science
Decay, interleaving, learning paths, knowledge gaps, and deep research.

### Phase 15 — Life Integration
Timeline, local-only mood, user-triggered ambient context, context restoration, and encrypted capsules.

### Phase 16 — Advanced Layer
Private wiki, growth metrics, evidence-backed ideas, offline/local-model boundary, and encrypted legacy handoff. Secret Vault scope includes TOTP, SSH-key storage, privacy-preserving breach checking, emergency kit, and encrypted export/import.

### Phase 17 — Cognix Core Integration
Source inbox expansion, claim review, translation versioning, fact-check workflow, research reports, and export integration. Document Assistant scope includes document-type classification, OCR review/low-confidence highlighting, appropriate medical/legal disclaimers, and Inbox → Processing → Review → Approved → Indexed → Archived → Deleted lifecycle. Language Tutor scope includes MM↔JP/KR reading/vocabulary/translation, parallel text, grammar explanations, JP furigana/romaji, KR romanization, TTS, writing correction, role-play, quizzes, and CEFR/JLPT/TOPIK mapping.

### Phase 18 — Vizora Lens
Batch media, richer OCR/vision, diagram/chart/infographic analysis, EXIF/document metadata, human review, media↔notes/concepts links, and Drive package export (original + OCR text + metadata JSON + thumbnail).

### Phase 19 — Native/Product UX
Offline-first reader, iOS/Android share-sheet capture, camera OCR, voice notes, push notifications, biometric Vault unlock, JP/KR native UI, accessibility, and responsive polish.

### Phase 20 — Production Engineering
Durable leases, backup/restore, migrations, observability, evaluation datasets, E2E, stress, security, and rollback. Evaluation scope includes AI grounding/hallucination/JSON, agent finding/synthesis quality, learning decay/path effectiveness, latency/storage/quota benchmarks, and prompt-injection/RLS/SSRF suites.

### Phase 21 — Release
Evidence index, approval/sign-off, release/tag preconditions, post-release smoke, rollback path, domains/TLS/secrets, and final production verification.

## Deferred / Guardrails

- Paid LLM activation remains deferred.
- Supabase Auth leaked-password protection remains a known Free-plan limitation until plan/settings support it.
- Future-phase autonomous/native/device runtime must not be activated before current release gates pass and release approval is recorded.
- A foundation, contract test, or CI PASS is not proof of production runtime acceptance.

## Release Blocker

Final production smoke and release/tag remain blocked by pending Book, browser, Sentry, recovery, mobile, accessibility, performance, GDPR, Render health/environment verification, grouped manual verification, and formal release approval.
