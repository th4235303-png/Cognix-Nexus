# Phase 20–21 Preparation Plan

> Preparation only. Production automation and release activation remain gated.

## Phase 20 — Production Engineering
Prepare:
- durable lease/heartbeat recovery tests
- backup/restore verification artifacts
- rollback rehearsal scripts/checklists
- observability event taxonomy and correlation IDs
- stress-test fixture definitions
- security regression/evaluation datasets
- release evidence retention

### Evaluation datasets
- AI: hallucination resistance, citation accuracy, structured JSON validity and grounding.
- Agent: finding quality, synthesis quality, evidence lineage and idempotency.
- Learning: decay prediction and learning-path effectiveness.
- Performance: latency, storage footprint and provider quota usage.
- Security: prompt injection, RLS ownership and SSRF.

Machine-readable seed fixtures live under docs/eval-fixtures/; they are deterministic preparation assets, not production PASS evidence.

Activation prerequisites:
1. real backup/restore evidence
2. rollback evidence
3. observability ingestion evidence
4. stress/security evidence

## Phase 21 — Final Release
Prepare:
- machine-readable release checklist
- gate evidence index
- approval/sign-off record
- release/tag preconditions
- post-release smoke checklist
- rollback decision record

Final activation requires every required gate to be PASS, including grouped manual verification, followed by final production smoke and release approval.

## Non-negotiable
Static documentation, scripts, or fixtures never substitute for production evidence. Release automation must fail closed when required evidence or approval is missing.
