# Phase 16 — Advanced Layer Foundation

> Status: **runtime implemented** — commit `3dc74b4`; 37 tests passing locally; pending push and migration apply on Supabase.

## Boundary

Phase 16 delivers wiki entity persistence (with source lineage), growth metric tracking (with derivation explainability), offline handoff records (artifact refs only — no payload), and secret refs (ciphertext refs only — no raw secrets). All flows enforce evidence and fail-closed.

## What was delivered (commit 3dc74b4)

| Artifact | Description |
|---|---|
| `app/services/advanced_layer/__init__.py` | Complete runtime exports — `WikiEntity`, `GrowthMetric`, `OfflineHandoff`, `SecretRef`, `BreachCheckRequest`, validators |
| `app/services/advanced_layer_service.py` | `persist_wiki_entity` (source_refs required), `persist_growth_metric` (evidence_refs + derivation required), `persist_offline_handoff` (artifact_ref only), `persist_secret_ref` (ciphertext_ref only) |
| `app/routers/advanced_layer.py` | POST/GET `/advanced/wiki-entities`, `/advanced/growth-metrics`, `/advanced/offline-handoffs`, `/advanced/secret-refs` |
| `migrations/037_phase16_advanced_layer_runtime.sql` | `advanced_wiki_entities`, `advanced_growth_metrics`, `advanced_offline_handoffs`, `advanced_secret_refs` — all with RLS initplan-safe pattern |
| `tests/test_phase16_advanced_layer.py` | 37 passing tests — contracts, allowlist validation, persist helpers (psycopg-stubbed for local) |

## Non-negotiable invariants (preserved)

1. WikiEntity requires at least one source_ref (lineage required).
2. GrowthMetric requires a derivation explanation and at least one evidence_ref.
3. OfflineHandoff stores only an artifact_ref (URI) — never the artifact payload.
4. SecretRef stores only ciphertext_ref — never raw secrets or plaintext.
5. BreachCheckRequest sends only a 5–6 char digest prefix — never the full hash/value.
6. All writes are owner-isolated and fail-closed.
