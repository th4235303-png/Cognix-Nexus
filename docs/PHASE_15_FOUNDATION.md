# Phase 15 — Life Integration Foundation

> Status: **runtime implemented** — commit `a542be3`; 27 tests passing locally; pending push and migration apply on Supabase.

## Boundary

Phase 15 delivers explicit user-triggered context restoration, consent events, and encrypted capsule references. All flows are owner-isolated and fail-closed. Ambient or implicit cross-feature behavior remains disabled.

## What was delivered (commit a542be3)

| Artifact | Description |
|---|---|
| `app/services/life_integration/__init__.py` | Complete runtime exports — `ContextRestoreRequest`, `PrivacyBoundary`, `EncryptedCapsuleRef`, `can_restore` |
| `app/services/life_integration_service.py` | `persist_restore_request` (consent + scope required), `persist_consent_event`, `persist_capsule_ref` (ciphertext_ref only — fail-closed) |
| `app/routers/life_integration.py` | POST/GET `/life/restore-requests`, POST/GET `/life/consent-events`, POST/GET `/life/capsule-refs` |
| `migrations/036_phase15_life_integration_runtime.sql` | `life_restore_requests`, `life_consent_events`, `life_capsule_refs` — all with RLS initplan-safe pattern |
| `tests/test_phase15_life_integration.py` | 27 passing tests — contracts, validation, persist helpers (psycopg-stubbed for local) |

## Non-negotiable invariants (preserved)

1. Context restoration is explicit and user-triggered — never ambient.
2. Private signals have a separate privacy boundary (consent required).
3. Encrypted capsule refs record exportability without exposing ciphertext.
4. `can_restore()` fails closed when ownership, consent, or scope is missing.
5. All writes are owner-isolated and fail-closed.
