# Phase 20 — Production Operations Foundation

> Status: **runtime implemented** — commit `ce38983`; 42 tests passing locally (combined with Phase 21); pending push and migration apply on Supabase.

## Boundary

Phase 20 delivers gate evidence persistence and recovery drill recording. Gate evidence with status `pass` requires an `evidence_ref`. Recovery drills must be fully evidenced (`observed + recovered + evidence_ref`) before they are accepted. Fail-closed throughout.

## What was delivered (commit ce38983)

| Artifact | Description |
|---|---|
| `app/services/release_evidence/__init__.py` | Complete runtime exports — `GateEvidence`, `GateStatus`, `ReleaseDecision`, `release_is_ready`, `ReleaseChecklist`, `checklist_status`, `RecoveryDrill`, `recovery_is_evidenced` |
| `app/services/release_evidence_service.py` | `persist_gate_evidence` (pass requires evidence_ref; idempotency key prevents duplicates), `persist_recovery_drill` (`recovery_is_evidenced()` required) |
| `app/routers/release_evidence.py` | POST/GET `/release/gates`, POST/GET `/release/drills`, GET `/release/checklist`, POST/GET `/release/decisions` |
| `migrations/040_phase20_21_release_evidence_runtime.sql` | `release_gate_evidence` (idempotency_key UNIQUE, status CHECK), `release_recovery_drills` (kind CHECK), `release_decisions` (evidence JSONB NOT NULL) — all with RLS initplan-safe pattern |
| `tests/test_phase20_21_release_evidence.py` | 42 passing tests — gate evidence, recovery drills, checklist evaluation, release decisions (psycopg-stubbed for local) |

## Non-negotiable invariants (preserved)

1. Gate evidence with `status='pass'` requires a non-empty `evidence_ref` — fail-closed.
2. Idempotency key prevents duplicate gate evidence rows per gate/status/owner.
3. Recovery drills must satisfy `recovery_is_evidenced()` — `observed + recovered + evidence_ref` all required.
4. Fail-closed: incomplete drills and unattached pass gates are rejected.
5. All writes are owner-isolated with RLS.
