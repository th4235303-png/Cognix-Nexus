# Phase 17 — Core Integration Foundation

> Status: **runtime implemented** — commit `df09ee7`; 42 tests passing locally; pending push and migration apply on Supabase.

## Boundary

Phase 17 delivers evidence artifact persistence, document classification with lifecycle transitions, and parallel text alignment. All evidence is attached before any finding becomes canonical. Document lifecycle transitions enforce a valid state machine.

## What was delivered (commit df09ee7)

| Artifact | Description |
|---|---|
| `app/services/core_integration/__init__.py` | Complete runtime exports — `EvidenceArtifact`, `DocumentClassification`, `ParallelText`, `DocumentLifecycleTransition`, validators |
| `app/services/core_integration_service.py` | `persist_evidence_artifact` (source_ref required), `persist_document_classification` (confidence range validated), `apply_document_lifecycle_transition` (valid transitions enforced), `persist_parallel_text` (both languages required) |
| `app/routers/core_integration.py` | POST/GET `/core/evidence-artifacts`, `/core/document-classifications`, POST `/core/document-classifications/{id}/lifecycle`, POST/GET `/core/parallel-texts` |
| `migrations/038_phase17_core_integration_runtime.sql` | `core_evidence_artifacts`, `core_document_classifications`, `core_document_lifecycle_events`, `core_parallel_texts` — all with RLS initplan-safe pattern |
| `tests/test_phase17_core_integration.py` | 42 passing tests — contracts, lifecycle state machine, persist helpers (psycopg-stubbed for local) |

## Non-negotiable invariants (preserved)

1. No finding becomes canonical without evidence attached.
2. Document lifecycle transitions must follow the valid state machine.
3. Parallel text requires both source and target language text to be non-empty.
4. Classification confidence must be in [0.0, 1.0].
5. All writes are owner-isolated and fail-closed.
