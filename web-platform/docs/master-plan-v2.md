# 🧠 COGNIX BRAIN VAULT — UNIFIED MASTER PLAN v2.0

**Status:** FINAL LOCKED product specification  
**Platform:** Web + Mobile | Personal AI OS | 7-in-1 Brain Vault + Level Up 20

## 1. Product definition

Cognix Brain Vault is a personal second brain: capture books, PDFs, documents, notes, ideas, quotes, web sources, media, and sensitive secrets into one system; read, understand, connect, retrieve, practice, apply, create, decide, and protect them over time.

### Core promise

> AI does not merely answer from stored material; over time it builds a personal, evidence-traceable knowledge system.

### Out of scope

Creator Studio, social networking, real-time collaboration, public sharing, and community marketplace.

## 2. Core loop

Capture → Understand → Organize → Connect → Retrieve → Practice → Apply → Create → Decide.

Daily/weekly/monthly experiences include Daily Digest, Quick Capture, Continue Reading, Inbox Triage, review, contradiction review, graph exploration, growth/compounding reports, knowledge-gap analysis, and decay reminders.

## 3. Seven modules

1. **Long-Book AI Reader** — PDF/EPUB/DOCX, OCR, reader controls, highlights, notes, progress checkpoints, Book Chat, L1–L7 hierarchy, citations and analytics.
2. **Second Brain** — books, documents, notes, highlights, quotes, concepts, people, places, events, questions, insights, actions, vocabulary, web sources and media; tags, collections, backlinks, graph, hybrid search, canonical notes and Inbox Triage.
3. **Myanmar Document Assistant** — OCR, extraction and explanations for contracts, letters, forms, invoices, receipts, meeting notes, study material, medical/legal documents and business cards; low-confidence review and lifecycle controls.
4. **AI Language Tutor** — own-content learning, MM↔EN first, JP/KR reading support, parallel text, grammar, furigana/romanization, TTS, writing correction, role-play, quizzes and FSRS.
5. **Secret Vault** — client-side encryption, isolated from AI/search/embeddings/logs, password/TOTP/SSH/recovery features, auto-lock, biometric native support, encrypted export/import and plaintext-free audit logs.
6. **Research Intelligence (Cognix Core)** — web/news/RSS/manual sources, extraction, translation, claims, trust, fact-check flags, review/approval and Drive export.
7. **Media Intelligence (Vizora Lens)** — image/PDF/document validation, hashing, OCR, metadata, image analysis, review, approval and Drive export.

## 4. Level Up 20

### Tier 1 — AI Active Layer
- AI Agent Mode / background worker
- Synthesis Engine
- Decision Support
- Writing Assistant
- Feynman Mode

### Tier 2 — Learning Science
- Knowledge Decay Prediction
- Interleaving Mode
- Learning Path Generator
- Knowledge Gap Analysis
- Research Mode / Deep Dive

### Tier 3 — Life Integration
- Personal Timeline
- Mood-Aware Mode
- Ambient Learning
- Context Restoration
- Time Capsule

### Tier 4 — Advanced
- Personal Wiki
- Knowledge Compounding Visualization
- Idea Generator
- Offline-First AI
- Legacy Mode

All AI-derived output remains non-canonical until human review/confirmation where the product contract requires it. Decision support must expose evidence and disagreement rather than silently deciding for the user.

## 5. Architecture

- UI: Next.js + React + TypeScript + Tailwind; Expo native client
- Application: API, durable jobs, worker, scheduler, agent pipeline
- AI abstraction: provider-neutral text, vision and embedding routing
- Intelligence: retrieval, agents, synthesis, decision, writing and learning services
- Data: PostgreSQL/Supabase + pgvector; object storage for raw files
- Crypto: isolated client-side Secret Vault
- Export: Google Drive package contract

### Web/native boundary

Native focuses on capture, read, review, sync and ambient experiences. Heavy processing stays server-side. Offline cache is supported for reader, summaries, notes and review material; offline AI is optional and local.

### Local-first policies

Per document: Cloud AI Allowed, Local-Only, Process-then-Delete Original, Keep Original, or Do Not Index.

## 6. Processing and evidence

Book pipeline:

Upload → storage → extraction/OCR → page/section detection → smart chunks → L2/L3/L4/L5/L6/L7 → embeddings → entities/links → synthesis → principles → review → canonical note → SRS → agent analysis.

Every processing stage needs checkpoint, retry/error state, progress and source-span traceability.

Citations should retain source ID, page/section/chapter, character/token offsets, exact quote and OCR confidence where available.

Summary versions retain model/version, prompt version, input/output hashes, parent version and embedding metadata. Existing summaries are never overwritten.

## 7. Security and trust

Data classes: public-like, private, highly sensitive.

AI answer rules:
1. no evidence → say so;
2. show source spans;
3. label inference;
4. expose conflicts;
5. warn on low confidence;
6. never include Vault data;
7. add medical/legal context disclaimers;
8. prioritize canonical user-approved knowledge;
9. label AI summaries;
10. preserve exact quotes with source context.

Documents are untrusted data. Prompt injection must not become system instructions or tool authorization. Vault content never enters prompts.

Vault model:
Master Password → Argon2id → device master key → per-entry key → AES-256-GCM → ciphertext-only server.

## 8. Reliability and operations

Production must require durable persistence. /health is liveness; /ready is persistence readiness. Jobs use leases/locks, idempotency, retries with backoff, error logging and recoverable state. Raw files stay in object storage; temporary OCR data is retention-limited; agent findings use TTL where appropriate.

Free-tier survival: cache, batch, local processing where safe, quota tracking, provider abstraction, backoff, queueing, off-peak agents and embedding reuse.

## 9. Data model

Core: profiles, settings, sessions, devices.  
Library: books, chapters, chunks, book_files, documents.  
Evidence: summaries, source_spans, summary_versions, embeddings.  
Knowledge: notes, note_sources, tags, collections, concepts, concept_links, canonical_notes, inbox_items, wiki_pages, wiki_links, wiki_sources, wiki_versions.  
Research: sources, claims, processing_tasks, reviews, export_jobs, activity_events.  
Media: assets, ocr_results, image_analysis, media_links, media_reviews.  
Language: vocab, vocab_reviews, language_levels, quiz_results, feynman_sessions, feynman_explanations, feynman_scores.  
Intelligence: agent_jobs, agent_runs, agent_findings, agent_schedules, syntheses, synthesis_sources, synthesis_versions, decisions, decision_evidence, decision_options, decision_notes, writing_projects, writing_drafts, writing_citations, decay_predictions, retention_curves, interleaving_sets, interleaving_results, learning_paths, learning_path_items, learning_path_progress, knowledge_gaps, gap_recommendations, research_reports, research_sections, research_sources, ideas, idea_sources, idea_actions.  
Life: life_events, life_event_knowledge_links, mood_logs, mood_activities, mood_recommendations, ambient_sessions, ambient_audio, ambient_transcripts, context_snapshots, context_activities, time_capsules, time_capsule_contents, time_capsule_unlocks, growth_metrics, growth_snapshots.  
Vault: vault_entries, vault_audit_log, legacy_vaults, legacy_beneficiaries, legacy_unlock_conditions.  
System: jobs, job_locks, job_logs, ai_usage, notifications, search_history.

Storage: raw files → object storage; metadata → Postgres; vectors → pgvector; Vault/legacy → encrypted ciphertext.

## 10. Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Plan lock, mockups, threat model, test corpus, architecture audit | Planned |
| 1 | Foundation | Delivered |
| 2 | Book Reader + L1–L7 | Delivered |
| 3 | Second Brain + RAG + writing foundation | Delivered in foundation; full Writing Assistant remains |
| 4 | Learning + Feynman | Learning foundation delivered; Feynman remains |
| 5 | Cross-book + contradiction | Delivered |
| 6 | Document Assistant + OCR | Delivered |
| 7 | Secret Vault | Boundary delivered; full client crypto UX remains |
| 8 | Compounding + export | Export delivered; full visualization remains |
| 9 | AI Active Layer | Next implementation wave |
| 10 | Learning Science Layer | Planned |
| 11 | Life Integration | Planned |
| 12 | Advanced Layer | Planned |
| 13 | Cognix Core Research integration | Foundation exists; deeper research mode remains |
| 14 | Vizora Lens integration | Input boundary exists; richer media intelligence remains |
| 15 | Native polish + JP/KR + final testing | Planned |
| 16+ | Durability, async productionization, observability, E2E/evaluation, release engineering | Required before final release |

## 11. Quality gates

Target metrics include citation correctness/groundedness, OCR accuracy, summary completeness, Vault leak = 0, duplicate job rate = 0, agent finding accuracy, synthesis coherence, decision evidence coverage, writing citation rate, learning-path completion, recovery rate, sync success, latency, storage growth and quota usage.

Testing layers: unit, integration, E2E, AI evaluation, agent evaluation, learning evaluation, performance/stress and security/prompt-injection testing.

## 12. Documentation contract

Required documentation:
README.md, ARCHITECTURE.md, DATA_MODEL.md, SECURITY.md, PROMPTS.md, DECISIONS.md, ROADMAP.md, TROUBLESHOOTING.md, CHANGELOG.md, USER_GUIDE.md, AGENT.md, LEARNING.md, SYNTHESIS.md, INTEGRATION.md, plus operations/runbook documentation.

## 13. Locked principles / decision log

Local-first; user-approved truth; provider abstraction; Vault isolation; structured/versioned summaries; L1–L7 hierarchy; multi-provider routing; durable jobs with lease/lock/idempotency; raw chunks retained for citations; native capture/read/review boundary; source-span citations; untrusted-document prompt-injection boundary; revision/merge sync; canonical knowledge; human conflict review; agent findings never auto-approved; synthesis needs multiple sources; decisions expose multiple evidence paths; mood remains local-only; ambient mode is user-triggered; capsules and legacy data are encrypted; Wiki is private-first; ideas require evidence.

## 14. Final product boundary

Cognix Brain Vault is one shared foundation for Brain Vault, Cognix Core research intelligence and Vizora Lens media intelligence. The system is considered release-ready only after the remaining implementation phases, real persistence/integration tests, security/evaluation gates, native verification and final deployment smoke tests pass.

**Netlify development deployment remains intentionally paused until final release candidate approval.**


## Book Intelligence extension

The Long-Book AI Reader is a background knowledge-production workflow:

**Library/Inbox → fingerprint + duplicate gate → AI Reading Room → partial/final distillation → Knowledge Vault → cross-book lessons/derived books.**

The current reference corpus is 9 categories / 170 files. Exact duplicates stop before expensive processing, incomplete runs resume from durable checkpoints, partial results are viewable while processing, and cross-book synthesis preserves source/version lineage. Free-provider operation is quota-aware and resumable.

The detailed contract is documented in web-platform/docs/book-intelligence-product-spec.md.
