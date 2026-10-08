# Phase 13 — AI Active Layer Foundation

> Status: foundation only; not a release gate and not a production agent runtime.

## Boundary

Phase 13 will build durable agent lifecycle, evidence-bound findings, synthesis,
decision support, writing and Feynman workflows. The foundation deliberately
does not execute agents or introduce a new provider dependency.

## Stable contracts

The active-layer contracts define provider-agnostic boundaries for evidence,
findings, durable agent runs, and decisions.

## Non-negotiable invariants

1. No finding becomes canonical without review.
2. Evidence references remain attached to generated findings and decisions.
3. Agent execution must be idempotent and recoverable.
4. Provider failures fail closed.
5. Runtime orchestration is not activated until the current release is green.

## Next implementation slices

1. Persist agent runs and event history after the release gate is green.
2. Reuse existing lease/heartbeat semantics.
3. Add evidence validation and citation checks before review transitions.
4. Add provider adapters behind one interface.
5. Add evaluation fixtures before autonomous execution.
