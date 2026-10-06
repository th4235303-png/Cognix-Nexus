# Cognix Nexus — UI / Frontend Plan

> UI product/design requirements only. Current implementation and verification live in UI_STATUS.md.

## Product UX principles

1. Private workspace feel; no marketing-heavy layout.
2. Calm editorial typography.
3. Minimal animation.
4. Thin borders and layered surfaces.
5. Mobile-first capture; desktop-first review.
6. Evidence/citation state must be visually explicit.
7. Accessibility is part of definition-of-done.

## Phase 1 — UI foundation

- Formalize color/type/spacing/radius/shadow/motion tokens.
- Document component variants and states.
- Standardize loading, empty, error and permission states.
- Produce representative desktop/mobile mockups.

## Phase 2 — Core UX

- Dashboard information hierarchy.
- Book library upload/progress/filter UX.
- Reader chapter/TOC/highlight/note flow.
- Source inbox detail/retry/error matrix.
- Notes/backlinks/collections.
- Graph exploration.
- RAG chat with citation cards.
- Review Center evidence/edit workflow.
- Vault unlock/auto-lock/encrypted client flow.
- Settings/provider/security surfaces.

## Phase 3 — Advanced UX

- Agent dashboard/findings/review.
- Synthesis/decision/writing/Feynman workspaces.
- Learning paths/gaps.
- Timeline/context/time capsules.
- Private wiki/growth/ideas/legacy.
- Vizora media/OCR/review.
- Export queue/history/retry.

## Phase 4 — Responsive + accessibility

- Mobile capture-first layout.
- Desktop review-first layout.
- No horizontal overflow.
- Keyboard navigation.
- Focus indicators.
- Screen-reader labels/ARIA.
- Color contrast.
- Reduced motion.
- WCAG AA verification.

## Phase 5 — UI testing/release

- Playwright authenticated smoke suite.
- Upload → processing → review → retrieval UI flow.
- Citation rendering.
- Permission/session-expiry states.
- Offline/error states.
- Lighthouse performance/accessibility baseline.
- Mobile Expo smoke and device evaluation.

## Completion contract

The UI is complete only when the implemented surfaces satisfy the product rules above, the responsive/accessibility checks pass, the critical authenticated flow is smoke-tested, and the production release candidate is verified.

All UI changes land on main.