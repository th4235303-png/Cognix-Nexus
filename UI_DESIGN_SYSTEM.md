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

- Use a calm editorial hierarchy with clear headings, readable body text and compact metadata.
- Desktop layouts should prioritize review and comparison.
- Mobile layouts should prioritize capture, reading and focused actions.
- Avoid horizontal overflow at narrow widths.
- Use consistent page-header and section patterns.

## Surface and component rules

Shared components should define explicit states where applicable:

- default
- hover
- focus
- active
- disabled
- loading
- empty
- error
- permission denied

Prefer thin borders, layered surfaces, restrained elevation and clear action hierarchy.

## Evidence and AI states

Citation/evidence status must be visually distinguishable. Unsupported answers, pending review, partial/draft knowledge and approved/canonical knowledge must not look interchangeable.

## Responsive rules

- Mobile: capture-first, compact navigation, touch-friendly controls.
- Desktop: review-first, richer comparison and side-by-side evidence.
- No horizontal overflow.
- Preserve essential actions at narrow widths.

## Accessibility rules

- Keyboard navigation must be supported.
- Visible focus indicators are required.
- Use semantic headings and landmarks.
- Icon-only controls require accessible labels.
- Meet WCAG AA contrast expectations.
- Respect reduced-motion preferences.
- Session-expiry and permission-denied states must be explicit.

## Core surfaces

- App shell/navigation.
- Dashboard.
- Books/library and upload/progress.
- Reader/chapters/highlights/notes.
- Sources and processing.
- Review Center.
- Notes/backlinks/collections.
- Graph.
- RAG chat and citation cards.
- Vault unlock/auto-lock/encrypted state.
- Settings/security/provider states.
- Level Up, agent, synthesis, learning, timeline, wiki and Vizora surfaces.
- Export queue/history/retry.

## UI completion contract

UI completion requires:

1. Foundation tokens and shared states are normalized.
2. Core workflows are implemented.
3. Evidence/review states are explicit.
4. Responsive and accessibility behavior is verified.
5. Authenticated Playwright smoke passes.
6. Lighthouse baseline is captured.
7. Mobile Expo/device smoke is completed.
8. Production frontend smoke is completed.

Implementation status belongs in `CURRENT_STATE.md`; this document owns the design rules.
