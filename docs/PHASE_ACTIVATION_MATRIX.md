## Reconciled activation status — 2026-10-14

The Phase 13–21 runtime implementation commits are already present in main. Repository docs report 243/243 local tests, but database calls are stubbed in the described local suite. Therefore the matrix status means **code implemented / production activation blocked**, not production-ready or production-verified. Migrations 034–040 require isolated real-PostgreSQL validation, and current-main CI/CodeQL must be confirmed before release-candidate status.

Do not duplicate implementation work in the active backlog. First close P0 release verification, migration/RLS evidence, Render health/readiness and trustworthy live environment inventory, Book acceptance, authenticated browser/accessibility/performance, Sentry, GDPR, mobile, and real recovery/rollback. Then activate one phase at a time after release approval.

Detailed order: [docs/EXECUTION_PLAN_2026-10-14.md](EXECUTION_PLAN_2026-10-14.md).

---

# Cognix Nexus — Future Phase Activation Matrix

> Status: **runtime code complete** (Ph13–21, 243 tests). Production activation blocked until P0 release gates pass.

## Activation guard

Phase 13+ runtime activation is blocked until the current release gates are green and final manual verification is complete. Foundations, contracts, tests, documentation, and non-runtime adapters may be prepared in parallel.

The machine-readable control surface is `docs/PHASE_ACTIVATION_MANIFEST.json`.

## Phase sequence

| Phase | Runtime Code | Commit | Tests | Activation gate | First runtime action |
| --- | --- | --- | --- | --- | --- |
| 13 Active Layer | ✅ Ready | `e1bf06c` | 34/34 | release green + evidence lifecycle ready | persist agent runs/events |
| 14 Learning Science | ✅ Ready | `93c6a46` | 32/32 | Phase 13 durable evidence + evaluation fixtures | persisted learning events |
| 15 Life Integration | ✅ Ready | `a542be3` | 27/27 | recovery + GDPR/privacy evidence | explicit user-triggered restore |
| 16 Advanced Layer | ✅ Ready | `3dc74b4` | 37/37 | Phase 15 privacy/recovery evidence | reviewable advanced artifacts |
| 17 Core Integration | ✅ Ready | `df09ee7` | 42/42 | shared Phase 13 evidence API | source/claim/report/export lineage |
| 18 Vizora Lens | ✅ Ready | `3fbacad` | 29/29 | storage/provider + evidence lineage | media/OCR processing behind explicit gate |
| 19 Native/Product UX | ✅ Ready | `3fbacad` | (above) | device/EAS + accessibility/performance evidence | native capability activation |
| 20 Production Engineering | ✅ Ready | `ce38983` | 42/42 | production drill evidence | production automation |
| 21 Final Release | ✅ Ready | `ce38983` | (above) | every required gate + approval | final release/tag |

## Parallel-preparation rules

1. Do not turn foundation code into autonomous production execution before the guard is green.
2. Do not report static readiness as production PASS.
3. Keep owner scope, evidence lineage, fail-closed behavior, and auditability in every future contract.
4. Provider-specific activation stays behind the corresponding external gate.
5. Manual verification remains the final grouped step for the current release.
6. After release green, activate one phase at a time and require its evidence before enabling the next runtime layer.

## Current execution batches

### Batch 0 — Current release
- CI PASS confirmed on main commit `538520aa908c8fdadef0a38c7fba23fea8ca3fae` (run 38071211914); CodeQL PASS (run 38071211816)
- reconcile live Render service/blueprint drift and safely inventory environment variables
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
