# Cognix Nexus — Processing Pipeline

## Research source pipeline
New → queued → extracting → cleaning → translating → summarizing → key points → fact-check flagging → trust scoring → needs review → approved → Drive exported.

## Book pipeline
Upload → storage tier selection → durable book row → processing task → worker claim/lease → extraction → chapters → chunks → embeddings → retrieval index → review/ready state.

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