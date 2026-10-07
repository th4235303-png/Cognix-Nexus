# Cognix Nexus — Remaining Work

## 2026-10-07 production gate reconciliation

### External gates
- [ ] Real AI provider E2E — provider drill exists; requires safe secret-backed runtime.
- [ ] Google Drive OAuth/account drill — requires account-owner consent/refresh-token issuance.
- [ ] Supabase Storage real write/read/checksum drill.
- [ ] B2 large-file write/read/checksum drill.
- [ ] Authenticated Playwright production smoke.
- [ ] Mobile EAS/device smoke.
- [ ] Full WCAG keyboard/screen-reader/responsive sweep.
- [ ] Lighthouse/performance run.
- [ ] Production backup → restore → rollback drill.
- [ ] Final production smoke and release tag.

### Implemented in main
- [x] Phase 1–6 Book Intelligence implementation.
- [x] Phase 7–12 Knowledge Vault/review/synthesis foundation.
- [x] AI reading checkpoint/retry/backoff schema and worker logic.
- [x] Migration 031 live in Supabase.
- [x] Migration 032 live in Supabase.
- [x] Knowledge Vault frontend route and navigation.
- [x] Provider E2E harness for Cloudinary, Supabase Storage, B2, extraction, embeddings, RRF and cited LLM response.
- [x] Google Drive OAuth/export implementation and idempotent upsert path.
- [x] Security overrides and CodeQL workflow.
- [x] Main-only execution rule.

## Execution rule

**Verify → implement/fix → test → production verify → update evidence → main.**

Do not mark a real-infrastructure gate green from static code inspection.