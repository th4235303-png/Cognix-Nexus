# Cognix Nexus — Processing Pipeline

## Research source pipeline
New → queued → extracting → cleaning → translating → summarizing → key points → fact-check flagging → trust scoring → needs review → approved → Drive exported.

## Book pipeline

The long-book workflow is a background AI reading system, not a requirement for the user to manually read every book:

```text
Upload / import
→ fingerprint + duplicate gate
→ durable book/version
→ queue
→ extraction / OCR
→ page + section detection
→ chapters
→ smart chunks
→ embeddings
→ AI key extraction
→ chapter synthesis
→ book synthesis
→ knowledge distillation
→ category/topic indexing
→ Knowledge Vault
→ cross-book lesson packs / derived books

Exact duplicate → stop + link existing version
Incomplete prior run → resume latest checkpoint
```

Each durable stage records progress, checkpoint, retry/error state and source-span lineage.

### Duplicate gate

- Exact content fingerprint match: stop automatically; do not create a second expensive run.
- Likely same book with different bytes: flag for confirmation rather than silently merging.
- Existing incomplete version: resume from the latest safe checkpoint.
- Explicit reprocess: create a new processing version and idempotency key.

### AI reading and distillation

Do not send an entire book as one giant prompt. Use chunk → local extraction → chapter synthesis → book synthesis. Keep core ideas, principles/frameworks, definitions, important distinctions, examples, actions, evidence and caveats; reduce repetitive filler while retaining source lineage.

### Partial-progress contract

A book may expose completed chapter summaries and extracted keys before the whole book is complete. Progress must come from durable completed units, not a fake timer. Users can inspect date/time, book, category, stage, percentage, completed units, latest keys, pauses, retries and errors while processing continues.

### Cross-book synthesis

Stable knowledge items can later be grouped by category/topic and synthesized into lesson packs, study guides, concept books and derived books. Every derived artifact keeps a source/version manifest.

## Retrieval
Query → lexical/semantic candidates → evidence selection → RRF/ranking → source/chunk citations → optional LLM synthesis.

## Failure rules
- Provider failures are explicit; no silent memory-only fallback.
- Retryable failures use bounded retry/backoff.
- Worker jobs use durable leases/fencing.
- Storage writes and database state are designed for retry/idempotency.
- SSRF-sensitive fetching validates every redirect and transport destination.

## Verification
Production completion requires a real end-to-end run, not only unit tests or a manually calculated score.