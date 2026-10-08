# Phase 15 — Life Integration Foundation

> Status: preparation only; ambient or cross-feature behavior is not active.

## Stable boundary

Context restoration is explicit and user-triggered. Private signals have a separate privacy boundary. Encrypted capsules are references, not implicit cross-feature data sources.

## Contracts

- `ContextRestoreRequest` requires an explicit user-triggered request.
- `PrivacyBoundary` makes retention and cross-feature use explicit.
- `EncryptedCapsuleRef` records exportability without exposing ciphertext.
- `can_restore()` fails closed when ownership, consent, or scope is missing.

## Activation order

1. Complete recovery and privacy release gates.
2. Define auditable consent/revocation events.
3. Add encrypted export/import fixtures.
4. Add opt-in context restoration.
5. Keep ambient behavior disabled until a separate release gate exists.
