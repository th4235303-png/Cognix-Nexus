# Future Phase Foundation Map

> Preparation only. This does not mark any future phase as production-complete.
> Current release gates remain the highest priority.
>
> The ordered activation control surface is [PHASE_ACTIVATION_MATRIX.md](./PHASE_ACTIVATION_MATRIX.md).

## Phase 13 — AI Active Layer

Foundation is prepared in `app/services/active_layer` and `docs/PHASE_13_FOUNDATION.md`.

Activation order:
1. durable run/event persistence
2. lease/heartbeat reuse
3. evidence validation and citation checks
4. provider adapter interface
5. evaluation fixtures
6. runtime orchestration

## Phase 14 — Learning Science

Foundation is prepared in `app/services/learning_science` and `docs/PHASE_14_FOUNDATION.md`.

Boundary:
- learning signals remain derived from user-owned evidence and explicit user actions
- decay/interleaving algorithms remain deterministic and testable
- learning-path generation retains source/evidence references
- autonomous learning state is never canonical without an auditable event

Dependency: Phase 13 evidence/run lifecycle.

## Phase 15 — Life Integration

Foundation is prepared in `app/services/life_integration` and `docs/PHASE_15_FOUNDATION.md`.

Boundary:
- context restoration is explicit and user-triggered
- local/private signals have a separate privacy boundary
- encrypted capsules never become an implicit cross-feature data source
- ambient behavior remains opt-in

Dependency: privacy/recovery gates and Phase 13 evidence lifecycle.

## Phase 16 — Advanced Layer

Foundation is prepared in `app/services/advanced_layer` and `docs/PHASE_16_FOUNDATION.md`.

Boundary:
- private wiki entities preserve source lineage
- growth metrics are derived and explainable
- offline/local-model boundaries are explicit
- encrypted handoff is exportable and recoverable

Dependency: Phase 15 privacy boundary and production recovery evidence.

## Phase 17 — Cognix Core Integration

Foundation is prepared in `app/services/core_integration` and `docs/PHASE_17_FOUNDATION.md`.

Boundary:
- source inbox, claims, translations, fact checks, research reports and exports consume shared evidence contracts
- review states remain compatible with the existing human-review lifecycle
- generated API contracts remain typechecked in CI

Dependency: Phase 13 evidence contracts and current P1 UI/release evidence.

## Phase 18 — Vizora Lens

Foundation boundary is documented in `docs/PHASE_18_FOUNDATION.md`.

Preparation should reuse existing object-storage and evidence-lineage boundaries. Media/OCR additions remain provider-failure explicit.

## Phase 19 — Native/Product UX

Foundation boundary is documented in `docs/PHASE_19_FOUNDATION.md`.

Preparation should reuse web design-system tokens and existing API contracts. Device, offline, camera, voice and biometric capabilities remain separate release gates.

## Phase 20 — Production Engineering

Foundation boundary is documented in `docs/PHASE_20_FOUNDATION.md`.

CI already contains local database integration and isolated restore coverage. Production activation still requires real backup/restore, rollback, observability and stress evidence.

## Phase 21 — Release

Foundation boundary is documented in `docs/PHASE_21_FOUNDATION.md`.

Release activation remains gated by provider/storage drills, authenticated browser smoke, accessibility/performance, mobile/device verification, GDPR export/delete, production recovery/rollback, observability, final production smoke, and release approval/tag.

## Parallel-preparation rule

While the current release is blocked on real-world gates:
- prepare contracts, tests, documentation and non-runtime adapters
- do not activate autonomous execution
- do not claim production PASS from static code
- do not introduce future-phase providers unless required by an approved gate

## Recommended execution batches

### Batch 0 — current release
1. resolve CI failures
2. run provider/storage/Book acceptance with supplied secrets
3. run authenticated Playwright
4. close external release gates with evidence
5. perform grouped manual verification last
6. final production smoke/release approval

### Batch 1 — Phase 13 + 17
1. Phase 13 durable persistence/events
2. Phase 13 evidence validation
3. Phase 17 shared evidence/API integration
4. evaluation fixtures

### Batch 2 — Phase 14 + 15 + 16
1. Phase 14 learning runtime/evaluation
2. Phase 15 privacy/context integration after recovery evidence
3. Phase 16 advanced-layer activation after Phase 15

### Batch 3 — Phase 18 + 19
1. Phase 18 media/OCR contract expansion
2. Phase 19 native capability boundaries and device evidence

### Batch 4 — Phase 20 + 21
1. Phase 20 production engineering expansion
2. Phase 21 release automation and approval controls
