# Phase 14 — Learning Science

> Status: **runtime implemented** — commit `93c6a46`; 32 tests passing locally; pending push and migration 035 apply on Supabase.

## Stable boundary

Learning signals are derived from explicit user-owned events and retain evidence references.
Scheduling primitives are deterministic and testable. No autonomous learning state is activated
without explicit review.

## What was delivered (commit 93c6a46)

| Artifact | Description |
|---|---|
| `app/services/learning_science/__init__.py` | Complete runtime exports — LearningSignal, LearningPathItem, decay_weight, LearningCandidate, priority, build_path |
| `app/services/learning_science_service.py` | `persist_learning_signal` (idempotent, evidence-required, signal_type + strength validated), `persist_learning_path` (evidence-required per item), `build_path_from_db` (decay-ranked from DB signals, no LLM) |
| `app/routers/learning_science.py` | POST/GET `/learning/signals`, GET/POST `/learning/path`, GET `/learning/path/items`, PATCH `/learning/path/{id}/review` |
| `migrations/035_phase14_learning_science_runtime.sql` | `learning_signals` (idempotency unique, signal_type CHECK, strength FLOAT CHECK, RLS initplan-safe), `learning_path_items` (reason NOT NULL+CHECK, review_state CHECK, RLS) |
| `tests/test_phase14_learning_science.py` | 32 passing tests — decay_weight invariants, contracts, priority ranking, build_path ordering, all no-DB validation paths |

## Invariants (preserved)

1. No learning path becomes active without an explicit reason.
2. Evidence refs must be attached to every persisted signal.
3. `decay_weight()` is deterministic — no override at runtime.
4. Signals are append-only; no UPDATE of existing signals.

## Next: Phase 15
