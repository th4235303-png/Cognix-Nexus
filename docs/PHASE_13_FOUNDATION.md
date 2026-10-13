# Phase 13 — AI Active Layer

> Status: **runtime implemented** — commit `e1bf06c`; 34 tests passing locally; pending push and migration apply on Supabase.

## Boundary

Phase 13 delivers durable agent lifecycle events, evidence-bound findings, synthesis,
decision support, writing and Feynman workflows. The runtime is now fully wired;
activation in production is gated on the P0 release guard being satisfied.

## What was delivered (commit e1bf06c)

| Artifact | Description |
|---|---|
| `app/services/active_layer/__init__.py` | Complete runtime exports — all contracts, events, execution and validation helpers |
| `app/services/agent.py` | `persist_lifecycle_event` (idempotent + terminal-fenced), `build_evidence_refs`, `persist_decision_record` (evidence-required, fail-closed) |
| `app/routers/brain_agent.py` | Fixed `owner_id` bug in `list_agent_jobs`/`list_findings`; new endpoints: GET/POST `/jobs/{id}/events`, POST `/jobs/{id}/decisions`, GET `/decisions`, PATCH `/decisions/{id}/review` |
| `migrations/034_phase13_active_layer_runtime.sql` | `agent_lifecycle_events` (idempotency key unique, RLS initplan-safe), `agent_decisions` (evidence JSONB NOT NULL, review_state CHECK), `agent_runs` extended with `evidence_refs` + `decision_ids` |
| `tests/test_phase13_runtime.py` | 34 passing tests — contracts, lifecycle events, execution decisions, build_evidence_refs, persist helpers (psycopg-stubbed for local) |

## Non-negotiable invariants (preserved)

1. No finding becomes canonical without review.
2. Evidence references remain attached to generated findings and decisions.
3. Agent execution must be idempotent and recoverable.
4. Provider failures fail closed.
5. Terminal runs cannot be revived (`terminal_event_is_fenced`).

## Next: Phase 14 (Learning Science)

Foundation already exists at `app/services/learning_science/`. Same pattern:
add runtime persistence, migration, tests.
