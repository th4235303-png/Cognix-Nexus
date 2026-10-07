# Cognix Nexus — UI Design System

> Owner: Frontend design/system
> Update when: UI tokens, shared component contracts, accessibility rules, or responsive layout principles change
> Last Updated: 2026-10-08
> Do NOT put here: live release evidence, tactical verification status, backend architecture, or provider credentials.

## Product UX principles
1. Private workspace feel; avoid marketing-heavy layouts.
2. Calm editorial typography.
3. Minimal animation.
4. Thin borders and layered surfaces.
5. Mobile-first capture; desktop-first review.
6. Evidence/citation state must be visually explicit.
7. Accessibility is part of definition-of-done.

## Design tokens
The existing frontend establishes semantic color, typography, spacing, radius, elevation/shadow, motion and focus tokens. New UI should consume shared semantic tokens rather than page-local magic values.

## Typography and layout
- Calm editorial hierarchy with clear headings and readable body text.
- Desktop prioritizes review and comparison.
- Mobile prioritizes capture, reading and focused actions.
- Avoid horizontal overflow.
- Use consistent page-header and section patterns.

## Component states
Shared components should define explicit states where applicable: default, hover, focus, active, disabled, loading, empty, error and permission denied.

## Evidence and AI states
Citation/evidence status must be visually distinguishable. Unsupported answers, pending review, partial/draft knowledge and approved/canonical knowledge must not look interchangeable.

## Responsive rules
- Mobile: capture-first, compact navigation, touch-friendly controls.
- Desktop: review-first, richer comparison and side-by-side evidence.
- Preserve essential actions at narrow widths.

## Accessibility rules
- Keyboard navigation.
- Visible focus indicators.
- Semantic headings and landmarks.
- Accessible labels for icon-only controls.
- WCAG AA contrast expectations.
- Reduced-motion support.
- Explicit session-expiry and permission-denied states.

## Core surfaces
App shell/navigation; dashboard; books/library and upload/progress; reader/chapters/highlights/notes; sources and processing; Review Center; notes/backlinks/collections; graph; RAG chat/citation cards; vault; settings/security/provider states; Level Up; agents; synthesis; learning; timeline; wiki; Vizora; export queue.

## UI completion contract
1. Foundation tokens and shared states normalized.
2. Core workflows implemented.
3. Evidence/review states explicit.
4. Responsive and accessibility behavior verified.
5. Authenticated Playwright smoke passes.
6. Lighthouse baseline captured.
7. Mobile Expo/device smoke completed.
8. Production frontend smoke completed.

Implementation status belongs in CURRENT_STATE.md; this document owns design rules.
