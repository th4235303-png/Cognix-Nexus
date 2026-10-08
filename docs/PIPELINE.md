# Cognix Nexus — Processing Pipeline

> Owner: Processing/platform
> Last Updated: 2026-10-08

## Canonical flow
Source/book → durable storage → extraction → chunks → embeddings/search → evidence selection → optional provider synthesis → citations → human review → approved knowledge → Brain Vault/learning.

## Durable stages
1. Ingest and fingerprint.
2. Persist source metadata and ownership.
3. Extract text/structure.
4. Create chunks with source lineage.
5. Generate embeddings and lexical indexes.
6. Retrieve and rank with hybrid RRF.
7. Produce derived artifacts with citations.
8. Keep outputs draft/needs-review until the required human gate.
9. Persist approved artifacts and downstream derived records.

## Failure behavior
Provider failures are explicit and fail closed. Jobs are resumable/idempotent. Duplicate fingerprints stop duplicate expensive processing. Partial results remain partial.

## Future extensions
- Phase 13: agent lifecycle, synthesis and decision support.
- Phase 17: broader source/claim/report/export integration.
- Phase 18: media/OCR/vision lineage.
- Phase 19: native capture and offline boundaries.
- Phase 20: recovery/observability/stress automation.

These are preparation/roadmap scope until their activation gates are satisfied.
