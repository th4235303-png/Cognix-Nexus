# Phase 18–19 Preparation Plan

> Preparation only. Runtime activation remains gated.

## Phase 18 — Vizora Lens
Prepare:
- batch media upload
- media/OCR/vision provider-neutral contracts
- richer diagram/chart/infographic analysis
- EXIF/document metadata extraction and deterministic normalization
- human review for OCR/image-analysis results and low confidence
- media↔notes/concepts links with owner/evidence lineage
- Drive package export: original + OCR text + metadata JSON + thumbnail
- successful/partial/failed extraction fixtures

Activation prerequisites:
1. storage provider live evidence
2. evidence lineage validation
3. provider-specific smoke
4. review workflow acceptance

No automatic media/OCR production processing is enabled by this preparation.

## Phase 19 — Native/Product UX
Prepare:
- full offline-first reader boundary
- iOS/Android share-sheet capture
- camera OCR interface
- voice-note capture
- push/reminder/digest notification consent and delivery boundary
- biometric Vault unlock boundary without server-side secret storage
- native JP/KR UI localization
- WCAG AA, keyboard, screen-reader and responsive test matrix
- EAS/device smoke checklist

Activation prerequisites:
1. Phase 18 lineage boundary where applicable
2. accessibility/performance evidence
3. EAS/device evidence
4. explicit platform capability consent

## Parallel rule
Phase 18–19 preparation may continue while release gates are pending, but device/provider runtime activation stays behind its corresponding external gate.
