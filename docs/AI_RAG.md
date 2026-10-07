# Cognix Nexus — AI & RAG

> Owner: AI/RAG pipeline
> Update when: retrieval, AI processing, evidence rules, or Book Intelligence behavior changes
> Last Updated: 2026-10-08
> Do NOT put here: provider secrets or release gate status.

## Research pipeline

New → Queued → Extracting → Cleaning → Translating → Summarizing → Key Points → Fact-check Flagging → Trust Scoring → Needs Review → Approved → Drive Exported.

## Book Intelligence pipeline

Upload/import
→ fingerprint + duplicate gate
→ durable book/version
→ queue
→ extraction/OCR
→ page/section detection
→ chapters
→ smart chunks
→ embeddings
→ AI key extraction
→ chapter synthesis
→ book synthesis
→ knowledge distillation
→ category/topic indexing
→ Knowledge Vault
→ cross-book lesson packs / derived books.

The worker is background/durable; the browser does not need to remain open.

## Duplicate and resume behavior

- Exact content fingerprint: stop duplicate expensive processing and link the existing version.
- Possible same-book match: flag for confirmation.
- Incomplete prior run: resume from latest safe checkpoint.
- Explicit reprocess: create a new processing version and idempotency key.

## Partial-progress contract

Completed chapter summaries/keys may be visible before whole-book completion. Progress comes from durable completed units, checkpoints, retries, pauses and errors, not a fake client timer.

## Knowledge distillation

Use:

chunk → local extraction → chapter synthesis → book synthesis → distillation.

Do not send a whole long book as one giant prompt. Preserve core ideas, principles, definitions, distinctions, examples, actions, evidence and caveats while reducing repetitive filler.

## Retrieval

Current retrieval is hybrid lexical/semantic candidate selection followed by evidence selection and RRF/ranking, source/chunk citations, and optional LLM synthesis.

Historical vector-only/non-semantic wording is retained only in archive material.

## Evidence-first AI

AI output is derived evidence, not canonical truth. Human review remains required where the product contract says approval is required.

## Cross-book synthesis

Lesson packs, study guides, concept books and derived books preserve source/version manifests and distinguish agreement, disagreement and inference.

## Provider behavior

The backend uses an OpenAI-compatible provider abstraction. The checked-in production blueprint has historically targeted an OpenAI-compatible endpoint; the exact live provider/credentials remain a verification concern. Do not claim direct OpenAI production activation without evidence.

## Reliability

Retryable failures use bounded retry/backoff. Worker jobs use durable leases/fencing. Provider failures are explicit and do not silently fall back to memory.
