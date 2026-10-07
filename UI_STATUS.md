# Cognix Nexus — UI Implementation Status

> Live UI implementation checklist. Design requirements live in UI_PLAN.md; production evidence lives in PRODUCTION_STATUS.md.

## Verified foundation — 2026-10-06

| Surface | Status | Evidence |
|---|---|---|
| Next.js / React / TypeScript | 🟢 | Existing frontend project |
| Tailwind + shadcn-style UI | 🟢 | Existing component system and globals |
| App shell / sidebar / mobile menu | 🟢 | Existing layout/header/navigation components |
| Dashboard / sources / processing / review | 🟢 | Existing route surfaces |
| Brain Vault routes | 🟢 | Existing books/reader/notes/graph/chat surfaces |
| Level Up workspace | 🟢 | Existing Level Up surface |
| Vault / export / Vizora | 🟢 | Existing product surfaces |
| Loading / empty / error states | 🟡 | Present in several surfaces; needs system-wide normalization |
| Design tokens | 🟢 | Semantic spacing/radius/motion/focus tokens added to globals.css |
| Responsive verification | 🟡 | Code has responsive classes; device verification pending |
| Accessibility | 🟡 | Some ARIA/semantic patterns exist; full WCAG verification pending |
| Authenticated Playwright smoke | 🔴 | Not production-verified |
| Lighthouse baseline | 🔴 | Not recorded |
| Mobile device/EAS smoke | 🔴 | Not production-verified |

## P1.1 Foundation completion

- [x] Formal token inventory: color, typography, spacing, radius, elevation, motion.
- [ ] Component state matrix: default, hover, focus, active, disabled, loading, empty, error, permission. Focus utility and keyboard-visible affordances are now established.
- [ ] Shared page-header and section patterns.
- [ ] Shared data-table/list patterns.
- [ ] Shared async feedback/toast pattern.
- [ ] Shared confirmation/destructive-action pattern.

## P1.2 Core workflow completion

- [ ] Dashboard hierarchy and first-use guidance.
- [ ] Books: upload, progress, filtering, empty/error/retry.
- [ ] Reader: TOC, chapter navigation, highlights and notes.
- [ ] Sources: add, fetch, redirect/error, retry and processing handoff.
- [ ] Processing: progress, failed state, retry, stale task state.
- [ ] Review Center: evidence, edit, warning and approval states.
- [ ] Notes: backlinks, source references and collections.
- [ ] Graph: readable exploration and empty state.
- [ ] RAG chat: citation cards, evidence state and unsupported-answer state.
- [ ] Vault: unlock, auto-lock, encrypted/client-only state and destructive delete confirmation.
- [ ] Settings: account, security, provider/deferred-provider messaging.

## P1.3 Advanced surfaces

- [ ] Level Up dashboard and feature navigation.
- [ ] Agent jobs/findings/review.
- [ ] Synthesis/decision/writing/Feynman surfaces.
- [ ] Learning paths and knowledge gaps.
- [ ] Timeline/context/time capsule.
- [ ] Private wiki/growth/ideas/legacy.
- [ ] Vizora media/OCR/review.
- [ ] Export queue/history/retry.

## P1.4 Responsive + accessibility

- [ ] Mobile capture-first layout.
- [ ] Desktop review-first layout.
- [ ] Verify no horizontal overflow at narrow/mobile widths.
- [ ] Keyboard-only navigation. Navigation controls now have explicit focus-ring and accessible labels; full keyboard sweep remains.
- [ ] Visible focus indicators.
- [ ] Semantic headings and landmarks.
- [ ] Screen-reader labels/ARIA for icon-only controls.
- [ ] Color contrast/WCAG AA.
- [ ] Reduced-motion behavior.
- [ ] Session-expiry and permission-denied states.

## P1.5 Verification/release

- [ ] Authenticated Playwright smoke suite.
- [ ] Upload → processing → review → retrieval UI flow.
- [ ] Citation rendering and source navigation.
- [ ] Error/retry/offline states.
- [ ] Lighthouse performance/accessibility baseline.
- [ ] Mobile Expo smoke.
- [ ] Production Netlify smoke after UI gate.

## Execution order

1. Foundation/state normalization.
2. Core Brain Vault + research workflows.
3. RAG/evidence/review surfaces.
4. Level Up/Vizora/export polish.
5. Responsive/accessibility.
6. Playwright/Lighthouse/mobile verification.
7. Netlify production smoke.
8. Update PRODUCTION_STATUS.md and REMAINING_WORK.md.

All UI changes land on main. Paid LLM and Google Drive remain deferred and must not block UI completion.

## Book Intelligence verification status — 2026-10-07

| Capability | Status | Notes |
|---|---|---|
| 9-category / 170-file reference corpus | 🟡 Product input confirmed | Controlled corpus dry-run remains pending |
| Library / Inbox lifecycle | 🟡 Foundation exists | Lifecycle state normalization remains |
| AI Reading Room | 🟡 Spec locked | Background provider-backed E2E remains |
| Duplicate auto-stop | 🟡 Contract planned | Existing task idempotency foundation; book fingerprint E2E remains |
| Partial progress/history | 🟡 Spec locked | Durable reading ledger implementation remains |
| Knowledge distillation | 🟡 Foundation exists | Book-level distillation UI/worker path remains |
| Category lesson packs | 🟡 Planned | Cross-book synthesis contract documented |
| Derived books | 🟡 Planned | Provenance/source-manifest contract documented |
| Markdown/plain-text reading ledger | 🟡 Planned | View/export contract documented |
