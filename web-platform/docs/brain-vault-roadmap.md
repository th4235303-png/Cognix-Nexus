# Cognix Brain Vault — Phase 1–11

The roadmap is deliberately evidence-first. A phase is considered implemented only when the corresponding API/data contract exists; vendor-dependent production integrations remain explicitly configurable.

| Phase | Scope | Current state |
| --- | --- | --- |
| 1 | PDF/EPUB ingestion + page/section spans + durable binary boundary | Implemented |
| 2 | Embeddings + pgvector semantic retrieval | Implemented, provider-configured |
| 3 | L1–L7 hierarchical book intelligence | Implemented, LLM-configured |
| 4 | Cross-book synthesis + contradiction review | Implemented, human review required |
| 5 | Language Tutor + spaced review | Implemented, FSRS-compatible scheduler foundation |
| 6 | Document Assistant + OCR | Implemented, Tesseract deployment dependency |
| 7 | Client-side Secret Vault | Implemented AES-GCM browser surface; KDF is PBKDF2 until an Argon2id WASM dependency is introduced |
| 8 | Unified export + cited RAG | Implemented JSON export and optional LLM citation synthesis |
| 9 | Expo mobile client | Foundation implemented; authenticated session handoff remains |
| 10 | Vizora Lens media input boundary | Foundation implemented through media/OCR ingestion API |
| 11 | Production hardening | Security headers, rate limiting, persistence checks, upload limits, advisory task locks, and dependency automation implemented |

## Non-negotiable boundaries

- AI output is not automatically canonical.
- Evidence citations remain attached to generated answers.
- Contradiction candidates require human confirmation.
- Secret plaintext is never sent to the server by the browser vault.
- Original book binaries use a storage abstraction and require persistent storage configuration.
- Semantic/RAG and OCR providers fail closed with explicit configuration errors.
