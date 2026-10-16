# Phase 21 — Release Readiness Foundation

> Status: **runtime implemented** — commit `ce38983`; 42 tests passing locally (combined with Phase 20); pending push and migration apply on Supabase.

## Boundary

Phase 21 delivers release checklist evaluation and release decision recording. A checklist evaluates all gate evidence rows and computes a `pass/fail/pending/blocked` status. Release decisions record the full evidence snapshot as JSONB — no secrets or binary payloads.

## What was delivered (commit ce38983)

| Artifact | Description |
|---|---|
| `app/services/release_evidence/__init__.py` | Exports `ReleaseChecklist`, `checklist_status`, `ReleaseDecision`, `release_is_ready` |
| `app/services/release_evidence_service.py` | `evaluate_release_checklist` (reads gate evidence rows, deduplicates by latest-first, calls `checklist_status()`), `persist_release_decision` (evidence JSONB required, non-empty) |
| `app/routers/release_evidence.py` | GET `/release/checklist?revision=&required_gates=`, POST/GET `/release/decisions` |
| `migrations/040_phase20_21_release_evidence_runtime.sql` | `release_decisions` (evidence JSONB NOT NULL DEFAULT '[]') — RLS initplan-safe |
| `tests/test_phase20_21_release_evidence.py` | Checklist + decision tests within 42-test suite — pass/fail/pending/blocked paths, deduplication, evidence snapshot |

## Non-negotiable invariants (preserved)

1. Release decisions require a non-empty evidence list — no evidence, no decision.
2. `checklist_status()` returns `blocked` for missing revision, `pending` for missing gates, `fail` for any non-pass gate or missing evidence_ref, `pass` only when all required gates pass with evidence attached.
3. `release_is_ready()` requires `approved=True`, all required gates passing, all with evidence_ref.
4. Evidence stored as JSONB — no secrets or binary data in evidence dicts.
5. All writes are owner-isolated with RLS.
