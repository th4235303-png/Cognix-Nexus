# Phase 14 — Learning Science Foundation

> Status: preparation only; no autonomous learning state is activated.

## Stable boundary

Learning signals are derived from explicit user-owned events and retain evidence references. Scheduling primitives are deterministic and testable.

## Contracts

- `LearningSignal` records a user-owned learning event without becoming a canonical profile by itself.
- `LearningPathItem` requires an explicit reason and evidence references.
- `decay_weight()` is deterministic and rejects invalid time parameters.

## Activation order

1. Phase 13 durable evidence/run lifecycle.
2. Evaluation fixtures for recall, interleaving and decay.
3. Persist auditable learning events.
4. Add reviewable path generation.
5. Only then consider runtime recommendations.
