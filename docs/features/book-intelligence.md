# Book Intelligence

> Owner: Book Intelligence feature
> Update when: lifecycle, duplicate policy, distillation, lesson-pack, derived-book, or reading-ledger behavior changes
> Last Updated: 2026-10-08
> Do NOT put here: generic UI tokens, live release evidence, or provider secrets.

## Goal
Book Intelligence is an AI reading and knowledge-production system. Users can upload/import books, leave the app, and later inspect progress, extracted knowledge and cross-book connections.

## Corpus
The planning reference corpus is 9 categories / 170 files. This is a controlled planning/dry-run count, not proof that all files are imported or processed in production.

## Lifecycle
Library / Inbox → duplicate + fingerprint gate → AI Reading Room → extraction/OCR → chapters/chunks → embeddings → AI key extraction → chapter synthesis → book synthesis → knowledge distillation → Knowledge Vault → cross-book synthesis.

## Duplicate policy
Exact fingerprint match: stop automatically and link the existing version. Possible same-book duplicate: flag for confirmation; do not silently merge. Explicit reprocess: create a new version and idempotency key.

## Partial progress and ledger
Completed chapters may publish partial/draft summaries and keys before final synthesis. Durable progress records date/time, book, category, stage, percentage, completed units, checkpoint, keys, pauses and errors. A Markdown/plain-text reading ledger is a planned durable/exportable view.

## Distillation
Use chunk → local extraction → chapter synthesis → book synthesis → distillation. Preserve principles, definitions, distinctions, examples, actions, evidence and caveats with source-span lineage.

## Cross-book synthesis
Lesson packs, study guides, concept books, contradiction maps and derived books preserve contributing source/version manifests and distinguish agreement, disagreement and inference.

## Safety invariants
- Partial knowledge is never represented as final.
- Original books remain separate from derived knowledge.
- Reprocessing creates a new version.
- Source lineage is retained.
- Provider quota/rate-limit behavior pauses safely and resumes from checkpoints.

## Status
Implementation foundation exists. Controlled corpus dry-run, lifecycle normalization, AI Reading Room E2E, duplicate fingerprint E2E, durable ledger, distillation, lesson packs, derived books and reading-ledger export remain pending/next work and are tracked in CURRENT_STATE/ROADMAP.
