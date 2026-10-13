# Phase 19 — Native/Product UX Foundation

> Status: **runtime implemented** — commit `3fbacad`; 29 tests passing locally (combined with Phase 18); pending push and migration apply on Supabase.

## Boundary

Phase 19 delivers device capability gate persistence. A capability gate is only recorded when it is activatable (`device_verified AND user_enabled`). Capability is constrained to a strict allowlist: `camera`, `voice`, `push`, `biometric`, `offline`.

## What was delivered (commit 3fbacad)

| Artifact | Description |
|---|---|
| `app/services/media_boundary/__init__.py` | Exports `DeviceGate`, `NativeCapability`, `capability_is_activatable` |
| `app/services/media_boundary_service.py` | `persist_device_gate` (capability allowlist + `capability_is_activatable()` required — fail-closed) |
| `app/routers/media_boundary.py` | POST/GET `/media/device-gates` |
| `migrations/039_phase18_19_media_boundary_runtime.sql` | `media_device_gates` (capability CHECK `IN ('camera','voice','push','biometric','offline')`) — RLS initplan-safe |
| `tests/test_phase18_19_media_boundary.py` | Device gate tests within 29-test suite — all capability and activatability invariants covered |

## Non-negotiable invariants (preserved)

1. Device gate only persisted when `capability_is_activatable()` returns True (`device_verified AND user_enabled`).
2. Capability must be one of: `camera`, `voice`, `push`, `biometric`, `offline` — any other value is rejected.
3. Fail-closed: inactive gates are not persisted.
4. All writes are owner-isolated and fail-closed.
