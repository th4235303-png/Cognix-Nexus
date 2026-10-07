# Cognix Brain Vault — Book Intelligence Product Specification

**Status:** Product behavior locked for implementation planning  
**Updated:** 2026-10-07

## Goal

The book system is an **AI reading and knowledge-production system**, not a requirement for the user to manually read every uploaded book. A user can upload/import books, leave the app, and later inspect what Cognix understood, how far processing reached, and how the resulting knowledge connects to other books.

## Current corpus

The current reference inventory is **9 categories / 170 files**:

1. Business, Entrepreneurship & Finance
2. Communication & Negotiation
3. Creativity & Tech
4. Future Tech
5. Leadership & Management
6. Productivity, Habits & Discipline
7. Psychology & Critical Thinking
8. Self-Help & Emotional Intelligence
9. Stoicism & Philosophy

This is a planning/dry-run corpus count, not proof that all 170 files are already imported or processed in production.

## Product lifecycle

```text
Library / Inbox
   ↓
Duplicate + fingerprint gate
   ↓
AI Reading Room
   ├─ extraction / OCR
   ├─ chapters / smart chunks
   ├─ embeddings
   ├─ AI key extraction
   ├─ chapter synthesis
   └─ book synthesis
   ↓
Knowledge Distillation
   ├─ principles
   ├─ concepts
   ├─ definitions
   ├─ examples
   ├─ actions / lessons
   └─ evidence / caveats
   ↓
Knowledge Vault / Completed
   ↓
Cross-book Synthesis
   ├─ category lessons
   ├─ study guides
   ├─ concept books
   └─ derived books
```

### 1. Library / Inbox

Preserve originals and source metadata: title, author, edition, category, file, storage provider, fingerprint, import date and processing version.

### 2. AI Reading Room

The worker performs the reading work in the background. The browser does not need to remain open. Processing is chunked, checkpointed, resumable and quota-aware.

### 3. Knowledge Vault / Completed

Derived knowledge is stored separately from originals and remains traceable to source book/version/chapter/chunk.

## Duplicate policy

**Exact duplicate:** stop automatically before expensive processing and link the new upload to the existing book/version.

**Possible same-book duplicate:** flag for confirmation; never silently merge different bytes.

**Explicit reprocess:** create a new version and idempotency key while retaining historical results.

## Partial progress

A partially processed book is still useful. Completed chapters can publish draft/partial summaries and extracted keys before the final book synthesis.

The progress ledger records date/time, book, category, stage, percentage, completed units, latest checkpoint, latest keys, retries, pauses and errors. Percentage must come from durable work units, not a fake timer.

Example:

```text
2026-10-07 | Business | Example Book | 42% | Ch. 4 complete
2026-10-07 | Business | Example Book | Key: customer discovery
2026-10-08 | Business | Example Book | 67% | paused: provider quota
```

This ledger remains viewable before completion and is available as Markdown/plain text.

## Knowledge distillation

Never send a long book as one giant prompt. Use:

```text
chunk → local extraction → chapter synthesis → book synthesis → distillation
```

Prefer useful material: core ideas, principles/frameworks, definitions, important distinctions, examples, actions, cause/effect, evidence and caveats. Reduce repetitive filler while retaining source lineage.

Each knowledge item records its source/version, chapter/chunk/span, type, confidence, processing version and review/canonical state.

## Cross-book synthesis

Stable knowledge can be recombined by category, topic, concept, skill or user-selected collection.

Outputs include lesson packs, study guides, practical playbooks, contradiction maps and derived books. Each output keeps a source/version manifest and distinguishes agreement, disagreement and inference.

## Derived books

A derived book is a new, source-linked knowledge artifact with title, purpose, category/topic, outline, chapters/lessons, source manifest, generation version, date and review state. It is not intended to silently reproduce source books verbatim.

## Free-provider / overnight behavior

Use batching, rate-limit handling, bounded retries, backoff, configured provider fallback, checkpoint/resume, quota-aware pausing and embedding reuse. “Run while I sleep” means the job is durable and can continue without the browser; it does not guarantee a free provider will finish overnight.

## Definition of done

- Exact duplicate upload stops duplicate processing.
- Interrupted jobs resume from a durable checkpoint.
- Partial summaries/keys are visible during processing.
- Reading ledger is durable and viewable.
- Multi-book category synthesis preserves source lineage.
- Derived books expose source manifests.
- Quota/rate-limit behavior pauses safely.
- The 9-category / 170-file corpus completes a controlled dry-run.
- UI, worker and database expose the same lifecycle.
