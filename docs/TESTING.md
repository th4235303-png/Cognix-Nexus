# Cognix Nexus — Testing & Verification

> Owner: Testing/release verification
> Update when: acceptance criteria, test layers, or verification tooling changes
> Last Updated: 2026-10-08
> Do NOT put here: live pass/fail evidence; that belongs in CURRENT_STATE.

## Test layers
1. Static/code checks.
2. Unit/integration tests.
3. Provider E2E drills.
4. Browser/authenticated Playwright.
5. Mobile/EAS/device verification.
6. Accessibility and performance.
7. Production restore/rollback.
8. Final production smoke.

## Core acceptance invariants
- AI output is not canonical without required review.
- Source/evidence lineage is retained.
- Owner isolation/RLS remains enforced.
- Provider failures are explicit.
- Durable jobs resume safely.
- Exact duplicate uploads do not trigger duplicate expensive processing.
- Partial knowledge is labeled partial/draft.
- Derived artifacts retain source/version manifests.

## External verification contract
Provider, OAuth, browser, device and production-recovery gates are not PASS from static code inspection alone. Run the real drill, capture evidence, clean up test objects, then promote status.

## Book Intelligence acceptance
9-category / 170-file controlled dry-run; exact duplicate auto-stop; checkpoint/resume; partial chapter summaries/keys; durable reading ledger; cross-book synthesis with lineage; derived books with source manifests; UI, worker and database expose the same lifecycle.

## UI acceptance
Authenticated upload → processing → review → retrieval; citation/source navigation; error/retry/offline states; keyboard/screen-reader/responsive checks; Lighthouse baseline; mobile Expo/device smoke.

## Release evidence
Use CURRENT_STATE.md for current gate state. Historical acceptance contracts are retained under archive/legacy/.

## Future evaluation datasets

Deterministic seed fixtures are maintained under `docs/eval-fixtures/` and scoped by domain:
- AI: grounding, hallucination resistance, citations, structured output.
- Agent: finding/synthesis quality, ownership, evidence lineage and idempotency.
- Learning: decay and learning-path effectiveness.
- Performance: latency, storage and provider quota usage.
- Security: prompt injection, RLS ownership and SSRF.

These fixtures are preparation assets only. They never substitute for real production gate evidence.

## Phase 13–21 prepared contract coverage

The prepared contract test `web-platform/backend/tests/test_phase13_21_prepared_contracts.py` covers:
- Phase 13: duplicate idempotency, terminal fencing and execution decisions.
- Phase 14: deterministic learning priority and path generation.
- Phase 15: explicit user-triggered restore, owner scope and privacy boundary.
- Phase 16: Secret Vault reference validation and privacy-preserving breach-prefix shape.
- Phase 17: Document Assistant classification/lifecycle and Language Tutor parallel-text boundaries.
- Phase 18: media package manifests and metadata safety.
- Phase 19: explicit device capability gates.
- Phase 20: recovery drill evidence requirements.
- Phase 21: release checklist evidence requirements.

These are deterministic preparation tests. They do not activate runtime, call external providers, or constitute production PASS.
