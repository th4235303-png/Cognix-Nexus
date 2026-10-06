# Cognix Nexus — UI / Frontend Plan

> UI roadmap and implementation status. Backend contracts are tracked separately.

## Current UI state — 2026-10-06

| Area | State |
|---|---|
| Next.js/React/TypeScript | 🟢 Implemented |
| Tailwind + shadcn foundation | 🟢 Present |
| App shell/sidebar/mobile nav | 🟢 Present |
| Core Brain Vault routes | 🟢 Present |
| Review/processing surfaces | 🟢 Present |
| Level Up workspace | 🟢 Present |
| Vault/export/Vizora surfaces | 🟢 Present |
| Design system | 🟡 Needs formal token/component documentation |
| Visual mockups | 🔴 Missing |
| Responsive verification | 🟡 Needs device-level verification |
| Accessibility | 🟡 Needs WCAG/keyboard/screen-reader verification |
| Playwright UI E2E | 🔴 Not yet production-verified |

## Existing routes/surfaces

Core: dashboard, books, reader, notes, graph, chat, source/review/processing, approved knowledge.

Product extensions: tutor, documents/OCR, vault, export, Vizora Lens, Level Up, delivery, usage, activity, settings.

## Phase 1 — UI foundation

- [ ] Formalize color/type/spacing/radius/shadow/motion tokens.
- [ ] Document component variants and states.
- [ ] Standardize loading, empty, error and permission states.
- [ ] Produce representative desktop/mobile mockups.

## Phase 2 — Core UX

- [ ] Dashboard information hierarchy.
- [ ] Book library upload/progress/filter UX.
- [ ] Reader chapter/TOC/highlight/note flow.
- [ ] Source inbox detail/retry/error matrix.
- [ ] Notes/backlinks/collections.
- [ ] Graph exploration.
- [ ] RAG chat with citation cards.
- [ ] Review Center evidence/edit workflow.
- [ ] Vault unlock/auto-lock/encrypted client flow.
- [ ] Settings/provider/security surfaces.

## Phase 3 — Advanced UX

- [ ] Agent dashboard/findings/review.
- [ ] Synthesis/decision/writing/Feynman workspaces.
- [ ] Learning paths/gaps.
- [ ] Timeline/context/time capsules.
- [ ] Private wiki/growth/ideas/legacy.
- [ ] Vizora media/OCR/review.
- [ ] Export queue/history/retry.

## Phase 4 — Responsive + accessibility

- [ ] Mobile capture-first layout.
- [ ] Desktop review-first layout.
- [ ] No horizontal overflow.
- [ ] Keyboard navigation.
- [ ] Focus indicators.
- [ ] Screen-reader labels/ARIA.
- [ ] Color contrast.
- [ ] Reduced motion.
- [ ] WCAG AA verification.

## Phase 5 — UI testing/release

- [ ] Playwright authenticated smoke suite.
- [ ] Upload → processing → review → retrieval UI flow.
- [ ] Citation rendering.
- [ ] Permission/session-expiry states.
- [ ] Offline/error states.
- [ ] Lighthouse performance/accessibility baseline.
- [ ] Mobile Expo smoke and device evaluation.

## Design rules

1. Private workspace feel; no marketing-heavy layout.
2. Calm editorial typography.
3. Minimal animation.
4. Thin borders and layered surfaces.
5. Mobile-first capture; desktop-first review.
6. Evidence/citation state must be visually explicit.
7. Accessibility is part of definition-of-done, not a later decoration.