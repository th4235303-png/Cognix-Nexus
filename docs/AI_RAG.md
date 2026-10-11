# Cognix Nexus — AI & RAG

> Owner: AI/RAG pipeline
> Update when: retrieval, AI processing, evidence rules, or Book Intelligence behavior changes
> Last Updated: 2026-10-11
> Do NOT put here: provider secrets or release gate status.

## Research pipeline
New → Queued → Extracting → Cleaning → Translating → Summarizing → Key Points → Fact-check Flagging → Trust Scoring → Needs Review → Approved → Drive Exported.

## Book Intelligence pipeline
Upload/import → fingerprint + duplicate gate → durable book/version → queue → extraction/OCR → page/section detection → chapters → smart chunks → embeddings → AI key extraction → chapter synthesis → book synthesis → knowledge distillation → category/topic indexing → Knowledge Vault → cross-book lesson packs / derived books.

The worker is background/durable; the browser does not need to remain open.

## Duplicate and resume behavior
- Exact content fingerprint: stop duplicate expensive processing and link the existing version.
- Possible same-book match: flag for confirmation.
- Incomplete prior run: resume from latest safe checkpoint.
- Explicit reprocess: create a new processing version and idempotency key.

## Partial-progress contract
Completed chapter summaries/keys may be visible before whole-book completion. Progress comes from durable completed units, checkpoints, retries, pauses and errors, not a fake client timer.

## Knowledge distillation
Use chunk → local extraction → chapter synthesis → book synthesis → distillation. Do not send a whole long book as one giant prompt. Preserve principles, definitions, distinctions, examples, actions, evidence and caveats with source-span lineage.

## Retrieval
Current retrieval is hybrid lexical/semantic candidate selection followed by evidence selection and RRF/ranking, source/chunk citations, and optional LLM synthesis. Historical vector-only/non-semantic wording is retained only in archive material.

## Evidence-first AI
AI output is derived evidence, not canonical truth. Human review remains required where the product contract says approval is required.

## Cross-book synthesis
Lesson packs, study guides, concept books and derived books preserve source/version manifests and distinguish agreement, disagreement and inference.

## Provider behavior
The backend defines provider endpoints and model IDs in code in `app/services/llm.py`; routes are eligible when their provider keys are present. Render should hold credentials, not model/URL overrides. The current route registry includes Gemini, OpenRouter, Hugging Face, Mistral, Cohere, Groq and Cloudflare. A configured key is not proof of provider health; the real provider E2E must record success/failure. Embeddings are separately routed in `app/services/embeddings.py`; production remains fixed at 1536 dimensions, with Cohere currently the only compatible configured route.

## Reliability
Retryable failures use bounded retry/backoff. Worker jobs use durable leases/fencing. Provider failures are explicit and do not silently fall back to memory.
