# Cognix Core executable-workflow audit

Updated: 2026-10-01

This audit distinguishes implemented executable code from external activation that requires user credentials/accounts/devices.

## Executable workflow checks

| Area | Workflow | Status | Notes |
|---|---|---|---|
| Phase 0 | safety/acceptance contracts | implemented | Completion contract and tests exist. |
| Phases 1-2 | PDF/EPUB -> sections -> chunks -> durable book records | implemented | Upload path stores original binary and extracted source spans. |
| Phase 2 | L1-L7 summary generation | implemented | Summary generation route creates versioned rows and source links. |
| Phase 3 | semantic retrieval -> cited synthesis | implemented | Embedding index plus hybrid RRF retrieval plus optional LLM synthesis. |
| Phase 3 | notes/concepts/links | implemented | Durable CRUD and graph projection. |
| Phase 4 | language cards -> review -> scheduling | implemented | Persistent review state and due queue. |
| Phase 5 | contradiction candidates -> human review | implemented | Candidate creation is non-authoritative; review state is explicit. |
| Phase 6 | OCR/media normalization | implemented | Image ingestion, OCR boundary, storage metadata. |
| Phase 7 | encrypted vault write/read boundary | implemented | Ciphertext is accepted/stored; listing does not return ciphertext. |
| Phase 8 | export queue -> worker -> Drive | implemented | Queue is durable/idempotent; worker transition is service-layer code. Live Drive still requires OAuth. |
| Phase 9/13 | scheduled agent -> durable job -> lease -> run -> finding | implemented | Durable lease, retry, evidence loading, finding review boundary. |
| Phase 10 | decay/interleaving/gap/path | implemented | Calculation plus durable result records. |
| Phase 11 | timeline/context/capsule/wiki/growth/sync/legacy | implemented | Durable records and safety policies exist. |
| Phase 12 | readiness/rate-limit/observability/backup helper | implemented | Production guards and drill tooling exist; destructive restore remains manual. |
| Phase 14 | research mode | implemented | Source-bound claims and review status. |
| Phase 15 | media intelligence boundary | implemented | Ingestion/OCR/storage boundary; live vision provider remains external. |
| Level Up 20 | feature matrix and core contracts | implemented | 20 feature contracts have executable service/route coverage. |

## Gaps found and addressed in this audit

1. Export worker depended on importing a router endpoint. Moved the state transition into the export service; API and worker now share the same service workflow.
2. Vault list endpoint returned ciphertext. It now returns metadata only.
3. Semantic RAG was vector-only despite the hybrid-RRF decision. Retrieval now combines semantic and lexical rankings with reciprocal-rank fusion.

## Remaining external activation

These are not code blockers and are intentionally not fabricated:
- real R2 credentials/bucket
- Google OAuth client and refresh token
- production LLM and embedding provider credentials
- Expo/EAS signing and physical-device verification
- production deployment/account activation
- real backup/restore drill against a disposable database

## Verification rule

Every code change must pass backend compile/unit tests, frontend typecheck/lint/build, and mobile configuration checks before being treated as complete.