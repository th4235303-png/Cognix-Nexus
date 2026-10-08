# Future Phase Foundation Map

> Preparation only. This does not mark any future phase as production-complete.
> Current release gates remain the highest priority.

## Phase 13 — AI Active Layer
Foundation is prepared in the backend active_layer package and PHASE_13_FOUNDATION.md.

Next activation:
1. durable run/event persistence
2. lease/heartbeat reuse
3. evidence validation and citation checks
4. provider adapter interface
5. evaluation fixtures
6. runtime orchestration

## Phase 14 — Learning Science
Preparation boundary:
- learning signals remain derived from user-owned evidence and explicit user actions
- decay/interleaving algorithms are deterministic and testable
- learning-path generation retains source/evidence references
- autonomous learning state is never canonical without an auditable event

Dependency: Phase 13 evidence/run lifecycle.

## Phase 15 — Life Integration
Preparation boundary:
- context restoration is explicit and user-triggered
- local-only/private signals have a separate privacy boundary
- encrypted capsules never become an implicit cross-feature data source
- ambient behavior remains opt-in

Dependency: privacy/recovery gates and Phase 13 evidence lifecycle.

## Phase 16 — Advanced Layer
Preparation boundary:
- private wiki entities preserve source lineage
- growth metrics are derived and explainable
- offline/local-model boundaries are explicit
- encrypted legacy handoff is exportable and recoverable

Dependency: Phase 15 privacy boundary and production recovery evidence.

## Phase 17 — Cognix Core Integration
Preparation boundary:
- source inbox, claims, translation versions, fact checks, research reports and exports consume shared evidence contracts
- review states remain compatible with the existing human-review lifecycle
- API contracts are generated and typechecked in CI

Dependency: current P1 UI completion and Phase 13 evidence contracts.

## Phase 18 — Vizora Lens
Preparation should reuse existing object-storage and evidence-lineage boundaries. Media/OCR additions remain provider-failure explicit.

## Phase 19 — Native/Product UX
Preparation should reuse web design-system tokens and existing API contracts. Device, offline, camera, voice and biometric capabilities remain separate release gates.

## Phase 20 — Production Engineering
Current CI already contains local database integration and isolated restore coverage. Production activation still requires real backup/restore, rollback, observability and stress evidence.

## Phase 21 — Release
Release activation remains gated by provider/storage drills, authenticated browser smoke, accessibility/performance, mobile/device verification, GDPR export/delete, production recovery/rollback, observability, final production smoke, and release approval/tag.

## Parallel-preparation rule

While the current release is blocked on real-world gates:
- prepare contracts, tests, documentation and non-runtime adapters
- do not activate autonomous execution
- do not claim production PASS from static code
- do not introduce future-phase providers unless required by an approved gate

## Recommended batches

### Batch A — release-critical
1. resolve CI failures from new automated checks
2. run provider/storage/Book acceptance gates with supplied secrets
3. run authenticated Playwright
4. capture evidence and close external gates

### Batch B — immediately after release green
1. Phase 13 persistence/events
2. Phase 13 evidence validation
3. Phase 17 shared evidence/API integration

### Batch C — following
1. Phase 14 learning-science contracts and evaluation fixtures
2. Phase 18 media/OCR contract expansion
3. Phase 19 native capability boundaries

### Batch D — later
1. Phase 15 privacy/context integrations
2. Phase 16 advanced layer
3. Phase 20 production engineering expansion
4. Phase 21 release automation
