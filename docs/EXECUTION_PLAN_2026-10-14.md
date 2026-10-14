# Cognix Nexus — Reconciled Execution Plan
**As of:** 2026-10-14  
**Scope:** Planning/documentation only. This change does not modify application code, deploy services, apply migrations, or activate runtime features.

## Decision summary

The 2026-10-13 Phase 13–21 implementation commits are already present in main through ea010485390c82bed48853c8433802fdf30cab1a; they are not “pending push.” Repository documentation reports 243/243 local tests passing across these phases. The reported tests use psycopg stubs/mocked database paths, so they demonstrate local contract/validation behavior—not live PostgreSQL migration, RLS, concurrency, or production acceptance.

Therefore:
- Mark Phase 13–21 **implemented in repository / not production-accepted / activation blocked**.
- Do not schedule the same phase implementation work as if it were still missing.
- Do not equate code/tests with migration application or production activation.
- The current critical path is P0 release verification and safe database validation, not more feature coding.

## Current evidence boundary

| Item | Current classification | What would close it |
|---|---|---|
| Main revision | ea010485390c82bed48853c8433802fdf30cab1a | Recheck before each release-gate run |
| Phase 13–21 implementation | In main; repository docs report 243/243 local tests | CI on current main plus real PostgreSQL migration/integration tests |
| Migrations 034–040 | Present in repository; production application not evidenced | Apply/test against an isolated PostgreSQL target, inspect RLS/constraints, then explicitly verify live migration history |
| Latest-head CI/CodeQL | No combined commit statuses were returned for the inspected head; older passing runs do not cover it | Trigger and verify current-head CI and CodeQL |
| Provider E2E | PASS recorded for run [#38344416584](https://github.com/th4235303-png/Cognix-Nexus/actions/runs/38344416584) on revision c354aa1804a1ef473eb091bdfca45a9532eb2e8a | Rerun against the intended release revision if required by release policy |
| Render internal health | Internal /health 200 was observed in logs | Fresh external /health and /ready responses and post-deploy worker evidence |
| Render env inventory | Unverified; integration cannot enumerate live names | Safe live inventory from Render API/dashboard, compare names only, never print values |
| Render env comparison script | **Not trustworthy for live parity yet:** its os.getenv() reads the GitHub runner process, not Render service configuration | Correct the implementation to read the intended Render service configuration through an authorized API, redact values, add tests; until then do not use its comparison as live evidence |
| Browser/accessibility gates | Code exists, execution not evidenced; credential-dependent suites can skip | Run with authorized E2E account and confirm required tests ran rather than skipped |
| Book acceptance | Synthetic schema/contract check is not the 9-category/170-file corpus run | Run controlled corpus and verify lifecycle, duplicates, checkpoint/resume, ledger, provenance and exports |
| Recovery | CI ephemeral PostgreSQL restore is not production recovery | Confirm isolated target identity and cleanup/rollback plan, then backup → restore → verify → rollback drill |
| Sentry/GDPR/mobile/performance | Pending real evidence | Run each gate with the appropriate account/device and retain evidence |
| Final release | **Blocked** | All required gates PASS on one approved revision, grouped manual verification, final production smoke, explicit approval/tag |

## Execution order — do not reorder

### Batch 0 — establish trustworthy CI on current main
1. Trigger CI and CodeQL for current main; record exact revision, run links, and failures.
2. Fix any failures before treating the revision as a candidate.
3. Verify the release workflow's required gates are enabled and inspect job conclusions; optional workflow_dispatch inputs defaulting to false must not be mistaken for executed gates.
4. Confirm authenticated Playwright/accessibility tests actually executed; a credential-based skip is not a PASS.

### Batch 1 — migrations and runtime safety (isolated database first)
1. Review migrations 034–040 and their ordering/rollback implications.
2. Apply them to an isolated PostgreSQL database—not production—and run real database integration tests for constraints, idempotency, transactions, owner isolation/RLS, and lifecycle transitions.
3. Verify each router fails closed when persistence or owner context is unavailable.
4. Only after evidence and explicit release approval, plan a controlled production migration. Do not activate Phase 13+ autonomous behavior merely because the migration exists.

### Batch 2 — correct release-gate evidence collection
1. Correct and test Render environment parity checking so it reads Render service configuration, not runner variables.
2. Capture external API /health and /ready, worker startup/runtime evidence, and compare live environment-variable names to the blueprint. Do not print values or delete variables by guessed names.
3. Run provider/storage checks on the target release revision; preserve the previously passing provider run as historical evidence, not as proof for a newer revision.
4. Run Sentry ingestion and inspect the resulting event in the Sentry UI.

### Batch 3 — product acceptance
1. Run Book Intelligence's controlled 9-category / 170-file corpus with exact duplicate auto-stop, checkpoint/resume, durable progress ledger, partial results, source-linked distillation, derived-book lineage, and export.
2. Run authenticated production browser smoke.
3. Run WCAG keyboard/screen-reader/responsive checks and Lighthouse/performance baseline.
4. Run mobile EAS/device smoke.
5. Test real-account GDPR owner-data export/delete and Google Drive OAuth reauthorization, real export, and idempotent retry where applicable.

### Batch 4 — recovery, final verification, release
1. Confirm the recovery target is isolated, writable, and disposable; document cleanup and rollback before running any production-derived restore.
2. Perform backup → isolated restore → integrity/owner-scope checks → rollback/cleanup; retain evidence without credentials or personal data.
3. Perform grouped manual UI/workflow verification **last**, after automated/external gates.
4. Run final production smoke on the exact approved revision.
5. Release approval and tag only after every required gate is evidence-backed PASS.

## Phase 13–21 activation policy

The feature implementation is no longer the immediate backlog. Activation remains gated:
- Phase 13: validate real persistence, event fencing, leases/heartbeat and evidence-bound decisions.
- Phase 14: validate persisted learning signals/path items and deterministic scheduling against real DB data.
- Phase 15–16: require explicit consent, privacy boundaries, owner scope, recovery and GDPR evidence before restore/capsule/secret-related activation.
- Phase 17–19: validate evidence lineage, document/media lifecycle, device capability boundaries and real accessibility/device evidence.
- Phase 20–21: only record release/recovery outcomes after the underlying drills actually ran; an evidence row or boolean alone is not proof.
- Enable one phase at a time after the release guard is green, with rollback available. No autonomous runtime activation before approval.

## Rules for status updates

Use only these labels:
- **Implemented:** code is present.
- **Local tests pass:** tests ran locally; state whether DB/provider calls were stubbed.
- **CI PASS:** a completed workflow passed on the exact revision.
- **Production verified:** real target was exercised and evidence retained.
- **Blocked/Pending:** prerequisites or real evidence are missing.

Never promote one label to a stronger one without new evidence. This plan supersedes contradictory older roadmap statements that Phase 13–21 implementation is still merely foundation work, while preserving production gates as pending.