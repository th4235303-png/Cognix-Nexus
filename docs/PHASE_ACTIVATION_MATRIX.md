# Cognix Nexus — Future Phase Activation Matrix

Status: preparation only. No autonomous production activation is enabled by this document.

## Activation guard

Phase 13+ runtime activation is blocked until the current release gates are green and final manual verification is complete. Foundations, contracts, tests, documentation, and non-runtime adapters may be prepared in parallel.

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

This matrix is a planning/activation control surface only; it does not itself activate any runtime.
