# Cognix Nexus — Phase 13–17 Parallel Preparation Plan

> Preparation only. This document does not activate autonomous runtime.
> Current release gates remain the activation guard.

## Parallel workstream

While the release candidate is waiting on real-world gates, the future track is prepared in this order:

1. contracts
2. tests
3. persistence design
4. evidence model
5. documentation
6. non-runtime adapters
7. evaluation fixtures

## Phase 13 — AI Active Layer

### Contracts
- `EvidenceRef`, `Finding`, `AgentRun`, and `DecisionRecord` remain provider-agnostic.
- Findings and decisions require evidence before human review/canonical use.
- Provider failures fail closed.

### Persistence design
Existing `agent_jobs`, `agent_runs`, and `agent_findings` schema is treated as the durable baseline.
Before runtime activation, harden:
- explicit owner scope at the durable job/run/finding boundary
- append-only lifecycle events or equivalent auditable state transitions
- lease/heartbeat recovery
- idempotency and terminal-state fencing
- evidence references that survive provider retries

No schema migration is activated solely to anticipate future runtime; changes must be justified by tests and the activation gate.

### Tests
Required before activation:
- durable run creation/update
- retry does not duplicate terminal findings
- lease loss prevents stale completion
- evidence-less findings cannot become canonical
- owner mismatch fails closed
- provider error leaves auditable failure state

### Non-runtime adapter boundary
Adapters may normalize provider input/output and evidence references, but must not enqueue autonomous production work before the release guard is green.

## Phase 17 — Cognix Core Integration

### Shared evidence model
All source/claim/translation/fact-check/report/export artifacts must retain:
- owner scope
- evidence references
- review state
- stable artifact identity
- source lineage

### Tests
Required:
- draft artifacts are not review-ready
- review-ready artifacts require evidence
- owner-less artifacts fail closed
- evidence references remain stable across derived artifacts
- export/report adapters preserve lineage

### API preparation
Generated API contracts remain CI-generated and typechecked. Phase 17 integrations should consume the shared evidence boundary rather than create provider-specific evidence formats.

## Evaluation fixtures

Fixtures should be deterministic and small:
- evidence-present / evidence-missing
- owner-match / owner-mismatch
- draft / needs-review / reviewed
- provider-success / provider-failure
- retry / duplicate-idempotency cases
- derived-artifact lineage preservation

## Activation rule

The release sequence remains:

CI PASS
→ provider/storage/Book acceptance
→ authenticated browser smoke
→ recovery/GDPR/observability/accessibility/performance/mobile
→ grouped manual verification last
→ final production smoke
→ release approval
→ Phase 13 activation
→ Phase 14 → 15 → … → 21.

Parallel preparation never changes that order.
