# Completion and verification contract

## Scope

This document is the acceptance checklist for the Cognix Brain Vault target: the original Master Plan phases 0–15, Level Up 20, testing/security/recovery, and deployment readiness.

## Implemented in main

- Research foundation and human-review lifecycle.
- Brain Vault ingestion, reader, notes, graph, evidence retrieval, summaries, embeddings.
- Tutor scheduling, OCR/document assistant, encrypted Vault boundary, export/automation.
- Agent worker foundation with evidence-bound findings and no auto-approval.
- Vizora media analysis/review lineage and copyright status.
- Local-first/offline policy, mood-local policy, encrypted time-capsule boundary.
- Level Up 20 deterministic contracts and web workspace.
- Database migration registration for the new intelligence/reliability tables.
- Request IDs, security headers, bounded rate limiting, readiness fail-closed behavior.
- Render/Netlify deployment pause safeguards.

## Level Up safety invariants

1. Synthesis requires at least three distinct source IDs.
2. Decision support reports evidence coverage rather than selecting an outcome.
3. Writing checks that citations refer to declared sources.
4. Feynman mastery is an explicit threshold, not an assertion of truth.
5. Decay uses retention-risk math and does not infer sensitive mood data.
6. Interleaving requires two or more subjects.
7. Learning paths only use supplied library items.
8. Knowledge gaps remain explicit until covered by evidence.
9. Research mode remains source-bound and review-gated.
10. Timeline/context restoration only uses supplied events.
11. Mood storage is local-only by default.
12. Ambient learning is user-triggered; no continuous listening/location tracking.
13. Wiki projection is private by default.
14. Offline sync detects conflicting revisions instead of silently overwriting.
15. Legacy policy requires encrypted payloads and explicit beneficiary release.
16. Vault/capsule APIs never return plaintext ciphertext payloads after storage.

## Remaining external verification

The following require real infrastructure or credentials and therefore cannot be honestly marked live from CI alone:

- Supabase/PostgreSQL production migration execution and rollback drill.
- R2 object upload/download lifecycle and checksum restore drill.
- Real AI provider routing/fallback/quota behavior with provider credentials.
- Google Drive OAuth/export against a real account.
- Sentry/monitoring ingestion in production.
- Mobile EAS build, device testing, biometric vault verification, camera/voice/offline sync.
- JP/KR reading-level content evaluation with representative datasets.
- 50-page and 500-page performance tests on production-like storage/CPU.
- Disaster recovery restore from a real backup.
- Final Netlify/Render production activation.

Until those are verified, deployment remains intentionally paused.
