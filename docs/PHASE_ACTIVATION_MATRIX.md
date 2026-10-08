# Cognix Nexus — Future Phase Activation Matrix

Status: preparation only. No autonomous production activation is enabled by this document.

## Activation guard

Phase 13+ runtime activation is blocked until the current release gates are green and final manual verification is complete. Foundations, contracts, tests, documentation, and non-runtime adapters may be prepared in parallel.

The machine-readable control surface is `docs/PHASE_ACTIVATION_MANIFEST.json`.

## Phase sequence

| Phase | Prepared now | Activation gate | First runtime action |
| --- | --- | --- | --- |
| 13 Active Layer | contracts, evidence validation, tests, foundation docs | release green + evidence lifecycle ready | persist agent runs/events |
| 14 Learning Science | signals, path contracts, decay tests, docs | Phase 13 durable evidence + evaluation fixtures | persisted learning events |
| 15 Life Integration | context restore, privacy boundary, capsule refs, tests/docs | recovery + GDPR/privacy evidence | explicit user-triggered restore |
| 16 Advanced Layer | wiki/growth/offline contracts, boundary docs | Phase 15 privacy/recovery evidence | reviewable advanced artifacts |
| 17 Core Integration | evidence-bound artifact contracts/tests/docs | shared Phase 13 evidence API | source/claim/report/export lineage |
| 18 Vizora Lens | media/OCR boundary docs | storage/provider + evidence lineage | media/OCR processing behind explicit gate |
| 19 Native/Product UX | device/offline/camera/voice/biometric boundaries | device/EAS + accessibility/performance evidence | native capability activation |
| 20 Production Engineering | recovery/rollback/observability foundation | production drill evidence | production automation |
| 21 Final Release | release checklist and gate model | every required gate + approval | final release/tag |

## Parallel-preparation rules

1. Do not turn foundation code into autonomous production execution before the guard is green.
2. Do not report static readiness as production PASS.
3. Keep owner scope, evidence lineage, fail-closed behavior, and auditability in every future contract.
4. Provider-specific activation stays behind the corresponding external gate.
5. Manual verification remains the final grouped step for the current release.
6. After release green, activate one phase at a time and require its evidence before enabling the next runtime layer.

## Current execution batches

### Batch 0 — Current release
- CI failure resolution
- release-gate preflight
- provider/storage/Book acceptance evidence
- authenticated browser smoke
- recovery/GDPR/observability/accessibility/performance/mobile evidence
- final manual verification and production smoke

### Batch 1 — Phase 13/17
- durable agent-run/event persistence
- lease/heartbeat lifecycle
- evidence validation and citation checks
- shared evidence-bound artifact API
- evaluation fixtures

### Batch 2 — Phase 14/15/16
- learning event persistence and deterministic scheduling
- explicit context restore with privacy boundaries
- advanced artifacts and offline handoff boundaries

### Batch 3 — Phase 18/19
- media/OCR lineage adapters
- native/device capability boundaries
- EAS/device/accessibility/performance release checks

### Batch 4 — Phase 20/21
- production rollback/recovery automation
- observability evidence
- final release automation and approval controls

## Remaining work by phase

### Phase 13
- Harden durable agent lifecycle persistence.
- Add lease/heartbeat recovery and retry fencing.
- Integrate evidence references into persisted findings/decisions.
- Keep agent runtime disabled until release approval.

### Phase 14
- Persist learning events and review scheduling.
- Implement deterministic decay/interleaving/path generation.
- Add evaluation and owner-scope persistence checks.

### Phase 15
- Implement explicit context restore and encrypted time-capsule runtime.
- Enforce consent, owner scope, recovery, and GDPR evidence.
- Keep mood/ambient features opt-in and local/privacy-bounded.

### Phase 16
- Implement Personal Wiki, growth visualization, idea generation, and offline boundaries.
- Implement Secret Vault TOTP, SSH-key storage, k-anonymity breach checks, emergency kit, and encrypted export/import.
- Require recovery/privacy evidence before activation.

### Phase 17
- Implement Document Assistant classifier/OCR review/lifecycle.
- Implement Language Tutor MM↔JP/KR reading, grammar, romanization, TTS, correction, role-play, quizzes, and CEFR/JLPT/TOPIK mapping.
- Preserve evidence, review state, ownership, and source lineage for derived artifacts.

### Phase 18
- Implement batch media upload, richer OCR/vision, metadata normalization, review workflow, media links, and Drive package export.
- Add successful/partial/failed extraction evidence fixtures.

### Phase 19
- Implement offline reader, share-sheet/capture, camera OCR, voice capture, push notifications, biometric unlock, and JP/KR localization.
- Complete WCAG AA, responsive, keyboard/screen-reader, EAS/device evidence.

### Phase 20
- Complete production recovery/rollback drills, observability correlation/evidence retention, stress testing, and security regression runs.
- Turn evaluation datasets into repeatable release checks.

### Phase 21
- Finalize machine-readable release checklist, evidence index, approval/signoff controls, release/tag preconditions, post-release smoke, and rollback decision path.

This matrix and manifest are planning/activation controls only; they do not themselves activate any runtime.
