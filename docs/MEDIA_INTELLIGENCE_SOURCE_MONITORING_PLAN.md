# Media Intelligence — Personal Source Monitoring Plan

> Status: proposed / planning only
> Product home: Cognix Nexus, aligned with Vizora Lens and source-ingestion / knowledge workflows
> Audience: personal use first; multi-user/productization requires separate approval
> Last updated: 2026-10-13

## Goal

Let a user save source links once, organize them into categories, and automatically detect new content. For YouTube, detect newly published videos, retrieve available transcripts/captions, and create searchable, source-linked knowledge records. Later, support other source types through adapters rather than making the system YouTube-only.

Example categories: AI, coding, language learning, research, product/news, and custom labels. Category names and generated output should support English and Burmese, with user-selectable output language.

This is a planned feature, not an implemented or production-ready capability.

## User workflow

1. Add a YouTube channel URL or channel ID to a category.
2. Resolve and store the canonical channel ID and URL.
3. Poll the channel RSS feed on a configurable cadence (30 minutes is a proposed initial default).
4. Deduplicate by stable video ID and persist discovery state before processing.
5. Attempt transcript/caption retrieval when available and permitted; record language, retrieval method, timestamps when supplied, and failure reason.
6. Save a source-linked video record and enqueue optional AI processing.
7. Generate summaries, up to five key takeaways, category suggestions, and translations when configured and when transcript quality is sufficient.
8. Display items in a category dashboard; optional notifications/digests (Telegram is one possible adapter).
9. Allow retry, manual correction, source removal, and deletion/export.

## MVP scope

- Personal source registry with categories and channel metadata.
- YouTube RSS polling, configurable interval, backoff, and deduplication.
- Durable states such as discovered → transcript_pending → transcript_ready / transcript_unavailable → summarization_pending → ready / failed.
- Transcript records with source/video references and language metadata.
- Category feed sorted by publication/discovery time, with original video links.
- Manual retry and explicit status/error reasons for unavailable transcripts.
- English/Burmese UI labels and output-language preference.
- Local prototype support; production integration only after privacy, persistence, and operations decisions.

## AI features, delivered incrementally

1. **Summary:** configurable concise summary (initial target: three short paragraphs); disclose partial transcript coverage.
2. **Key takeaways:** up to five points linked to the original video; timestamp links only when reliable timestamps exist.
3. **Translation:** translate summaries or transcript excerpts into English or Burmese while preserving original text and language metadata.
4. **Auto-categorization:** suggest categories based on content, with user override.
5. **News/digests:** aggregate items by category/time window, cluster related stories, and retain links for each claim.
6. **Knowledge integration:** index transcript/summary records only after ownership, provenance, retention, and deletion rules are enforced.

AI output is derived content, not a replacement for the original source. Preserve generation time, provider/model and version metadata where appropriate, and support regeneration.

## Extensible source adapter

Define a generic source-ingestion contract with source type, canonical source ID/URL, display title, category assignments, published/discovered times, stable external item ID, source metadata, content/transcript status, language, processing state, retry/error fields, and provenance links from all derived records.

YouTube is the first adapter. Future candidates include RSS/Atom feeds, podcasts, selected blogs/news sites, newsletters, and user-submitted documents. Each adapter must define its permitted retrieval method, refresh policy, and content limitations.

## Provisional technical direction

- **Backend:** Python, reusing Cognix Nexus ingestion/job conventions where practical.
- **Discovery:** YouTube channel RSS pattern: `https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}`.
- **Parsing:** an RSS/Atom parser such as `feedparser`.
- **Transcript retrieval:** evaluate `youtube-transcript-api` as an optional dependency. Missing, disabled, restricted, or unsupported captions are normal outcomes, not fatal pipeline errors.
- **Persistence:** for integrated production use the existing database and owner-isolation conventions. SQLite/JSON may be used for a standalone local prototype, but should not become a competing production source of truth.
- **Background work:** use durable worker/job conventions; polling and processing must be idempotent and restart-safe.
- **UI:** category-based dashboard/feed first; Telegram behind an optional notification adapter.
- **AI:** provider-agnostic summarization/translation/categorization with quotas, retries, cost limits, and model metadata.
- **Scheduling:** configurable conservative polling (30 minutes proposed), bounded concurrency and backoff.

## Constraints and failure handling

- RSS indicates newly published items; it does not guarantee transcript availability.
- Never treat a missing transcript as a successful empty transcript or fabricate transcript text.
- Before implementation, verify current YouTube terms, library behavior, and applicable API requirements. Prefer official, permitted interfaces where feasible. Do not bypass access controls, paywalls, authentication, anti-bot controls, or platform restrictions.
- Keep original source links and provenance attached to summaries/digests; distinguish source facts from AI-generated interpretation.
- Respect rate limits, use backoff, handle at-least-once feed delivery through deduplication, and provide a pause/disable switch.
- Enforce owner isolation, retention/deletion behavior, and safe handling of untrusted transcript text, including prompt-injection attempts.
- Never commit OAuth tokens or API keys or print secrets in logs.
- Do not send full transcripts to third-party AI providers without explicit configuration/consent and clear privacy/cost boundaries.
- Show language and transcript quality/completeness; do not present uncertain translations/summaries as verified facts.
- Define whether source removal also deletes stored transcripts and derived records.

## Data model sketch (not a migration specification)

Potential entities to reconcile with the existing schema before coding:

- `media_sources`: owner, source type, canonical URL/ID, title, enabled flag, polling settings, last checked time/cursor, category membership.
- `media_items`: source ID, external item ID, canonical URL, title, published/discovered times, metadata, processing and transcript status, last error.
- `media_transcripts`: item ID, language, text/chunk references, retrieval method, timing/quality metadata, content hash.
- `media_derivatives`: item ID, type (summary/takeaways/translation/category suggestion), language, content, model/version metadata, provenance references.
- Reuse durable jobs or add a job entity only if existing infrastructure is insufficient.

Names are illustrative. Inspect existing data models and migration conventions before choosing actual tables. Categories should be user-defined and support multiple categories per source/item; do not hard-code only AI/Coding/Language or impose a 20-channel cap.

## Delivery phases and acceptance

### Phase A — Source registry and discovery
- Add/edit/disable/delete a source and assign it to a category.
- Support roughly 20 channels per category or more without a design limit of 20.
- Validate/canonicalize source URLs and IDs.
- Repeated polling and restarts do not create duplicate videos.
- Store published/discovered times and last-poll status.
- One source's failure does not stop other sources.

### Phase B — Transcript acquisition
- Retrieve transcripts when permitted and available, preserving language and reliable timing information.
- Represent unavailable/disabled/restricted captions explicitly.
- Retry transient failures with bounded backoff; do not retry permanent failures forever.
- Never fabricate missing transcript content.

### Phase C — AI derivatives and multilingual output
- Generate summaries and up to five takeaways with source references.
- Support English and Burmese output settings.
- Keep source transcript and generated derivatives separate.
- Make output language and transcript completeness visible.
- Retry/regenerate without duplicating records.

### Phase D — Dashboard and notifications
- Filter by category, source, publication date, transcript status, and processing status.
- Link every item to the original video.
- Optional Telegram notifications/digests with per-category preferences and rate limits.
- Digest entries link to original items and disclose transcript gaps.

### Phase E — Additional sources and knowledge integration
- Add RSS/Atom, podcast, and other approved adapters behind the generic contract.
- Integrate with Cognix Nexus knowledge search only after provenance, ownership, retention, and deletion semantics are tested.
- Add related-story clustering and periodic summaries after basic ingestion is reliable.

## Definition of done for first usable version

- Users can manage categories and multiple channel sources.
- Polling reliably discovers new videos and is idempotent across repeated runs/restarts.
- Transcript success/failure states are explicit and observable.
- Summaries, takeaways, and translations are optional, retryable, language-aware, and source-linked.
- One failed source/transcript does not block other queue work.
- Owner isolation, deletion behavior, secret handling, rate limiting, and untrusted-content defenses are tested.
- Tests cover RSS parsing, duplicates, retries, missing captions, language metadata, partial transcripts, AI failures, and per-owner access.
- No production readiness claim until deployed health, monitoring, and end-to-end acceptance are verified.

## Out of scope for the first version

- Downloading or re-hosting video media.
- Guaranteeing transcript access for every video.
- Autonomous public posting or third-party distribution without user configuration.
- Scraping that bypasses access restrictions.
- Treating AI summaries as authoritative without source links and coverage indicators.
- Enabling paid AI usage without an explicit budget/configuration decision.
