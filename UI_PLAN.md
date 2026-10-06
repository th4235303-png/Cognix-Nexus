# Cognix Nexus — UI / Frontend Plan

> **Frontend planning file.**
> Backend ကို အရင် ပြီးအောင်လုပ်ပြီးမှ UI ကို တည်ဆောက်။
> See `REMAINING_WORK.md` for backend tasks.

---

## Current State

| Item | Status |
|---|---|
| Frontend Framework | Next.js 14 + React + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Design System | ⚠️ Not defined |
| Mockup | ❌ Missing |
| Component Library | ⚠️ Partial |
| Routes | ⚠️ Partial |
| Responsive | ⚠️ Not tested |
| Accessibility | ⚠️ Not tested |

**Rule:** Backend Priority 0 ပြီးမှ UI ကို တည်ဆောက်။

---

## Phase 1 — UI Foundation (Backend ပြီးရင်)

### 1.1 Design System
- [ ] Color palette (deep navy-black + cyan + amber)
- [ ] Typography (editorial, calm)
- [ ] Spacing scale (4/8/16/24/32)
- [ ] Border radius
- [ ] Shadow levels
- [ ] Animation (minimal)

### 1.2 Layout
- [ ] Root layout
- [ ] Sidebar (collapsible)
- [ ] Header (search + user)
- [ ] Main content area
- [ ] Footer (minimal)

### 1.3 Component Library
- [ ] Button (primary, secondary, ghost, danger)
- [ ] Input (text, search, textarea)
- [ ] Select / Combobox
- [ ] Checkbox / Radio / Switch
- [ ] Modal / Dialog / Drawer
- [ ] Toast / Notification
- [ ] Badge / Status pill
- [ ] Card / Panel
- [ ] Table / List
- [ ] Tabs
- [ ] Tooltip
- [ ] Skeleton / Loading
- [ ] Empty state
- [ ] Error state

---

## Phase 2 — Core UI Pages

### 2.1 Dashboard

┌─────────────────────────────────────┐
│ Dashboard │
├─────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ │
│ │ Books │ │ Notes │ │
│ │ 12 │ │ 234 │ │
│ └──────────┘ └──────────┘ │
│ ┌──────────┐ ┌──────────┐ │
│ │ Sources │ │ Embeddings│ │
│ │ 45 │ │ 1,234 │ │
│ └──────────┘ └──────────┘ │
│ │
│ Recent Activity │
│ - Book "Atomic Habits" uploaded │
│ - Source "Logistics" processed │
│ - Note "Focus System" created │
└─────────────────────────────────────┘

text

### 2.2 Book Library
- [ ] Grid view / List view toggle
- [ ] Search + Filter
- [ ] Upload button (drag & drop)
- [ ] Book card (cover, title, author, progress)
- [ ] Sort (recent, title, progress)

### 2.3 Book Reader
- [ ] Chapter navigation
- [ ] Highlight + Note
- [ ] TOC sidebar
- [ ] Font / Theme toggle
- [ ] TTS controls
- [ ] Progress bar
- [ ] Book chat (sidebar)

### 2.4 Source Inbox
- [ ] Add URL input
- [ ] Manual note
- [ ] Status pills (queued, processing, done, failed)
- [ ] List view
- [ ] Detail drawer

### 2.5 Notes
- [ ] Note list
- [ ] Note editor (Markdown)
- [ ] Backlinks panel
- [ ] Tags + Collections
- [ ] Source links

### 2.6 Knowledge Graph
- [ ] Force-directed graph
- [ ] Node types (Book, Note, Concept)
- [ ] Filter
- [ ] Zoom + Pan
- [ ] Click → detail

### 2.7 Chat (RAG)
- [ ] Message list
- [ ] Input box
- [ ] Citation cards
- [ ] Source link
- [ ] Streaming response

### 2.8 Review Center
- [ ] Queue list
- [ ] 3-column layout (queue | evidence | edit)
- [ ] Approve / Reject / Revision buttons
- [ ] Checklist
- [ ] Warning display

### 2.9 Vault
- [ ] Vault unlock screen
- [ ] Entry list
- [ ] Entry detail
- [ ] Password generator
- [ ] TOTP display
- [ ] Auto-lock timer

### 2.10 Settings
- [ ] Profile
- [ ] Appearance (theme, font)
- [ ] Storage
- [ ] AI Providers
- [ ] Notifications
- [ ] Security

---

## Phase 3 — Advanced UI

### 3.1 Level Up Pages
- [ ] Agent dashboard
- [ ] Synthesis viewer
- [ ] Decision workspace
- [ ] Writing editor
- [ ] Feynman mode UI
- [ ] Learning paths
- [ ] Knowledge gaps
- [ ] Timeline
- [ ] Mood log
- [ ] Ambient player
- [ ] Context restore
- [ ] Time capsules
- [ ] Personal wiki
- [ ] Growth metrics
- [ ] Idea generator
- [ ] Legacy mode

### 3.2 Media (Vizora)
- [ ] Media library
- [ ] Image viewer
- [ ] OCR result viewer
- [ ] Batch upload
- [ ] Batch review

### 3.3 Document Assistant
- [ ] Document list
- [ ] Document detail
- [ ] Extracted fields
- [ ] Review screen

### 3.4 Export
- [ ] Export queue
- [ ] Export detail
- [ ] Drive history
- [ ] Retry failed

---

## Phase 4 — Design System Detail

### 4.1 Color Palette (Suggested)

| Token | Value | Use |
|---|---|---|
| `bg-primary` | #0A0E1A | Deep navy-black |
| `bg-surface` | #111827 | Card surface |
| `accent-primary` | #06B6D4 | Muted cyan |
| `accent-secondary` | #8B5CF6 | Violet |
| `text-primary` | #F9FAFB | Main text |
| `text-muted` | #9CA3AF | Secondary |
| `border` | #1F2937 | Thin border |
| `warning` | #F59E0B | Amber |
| `success` | #10B981 | Green |
| `error` | #EF4444 | Red |

### 4.2 Typography

| Element | Font | Size |
|---|---|---|
| Heading 1 | Inter | 32px |
| Heading 2 | Inter | 24px |
| Heading 3 | Inter | 20px |
| Body | Inter | 16px |
| Small | Inter | 14px |
| Caption | Inter | 12px |
| Code | JetBrains Mono | 14px |

### 4.3 Spacing Scale
4px → xs
8px → sm
16px → md
24px → lg
32px → xl
48px → 2xl
64px → 3xl

text

---

## Phase 5 — Responsive Design

### 5.1 Breakpoints
| Breakpoint | Width |
|---|---|
| Mobile | <640px |
| Tablet | 640-1024px |
| Desktop | >1024px |

### 5.2 Mobile Layout
- [ ] Hamburger navigation
- [ ] Card/list layout
- [ ] Full-width forms
- [ ] Bottom-sheet filters
- [ ] Sticky action bar
- [ ] No horizontal overflow

### 5.3 Tablet Layout
- [ ] Collapsible sidebar
- [ ] Reduced columns
- [ ] Stacked metadata
- [ ] Slide-in drawers

---

## Phase 6 — Accessibility

- [ ] WCAG AA compliance
- [ ] Keyboard navigation
- [ ] Focus indicators
- [ ] Screen reader labels
- [ ] ARIA attributes
- [ ] Color contrast
- [ ] Reduced motion support

---

## Phase 7 — UX Patterns

### 7.1 Loading States
- [ ] Skeleton loaders
- [ ] Progress bars
- [ ] Spinners (minimal)
- [ ] Optimistic updates

### 7.2 Empty States
- [ ] No books
- [ ] No notes
- [ ] No sources
- [ ] No results
- [ ] No data

### 7.3 Error States
- [ ] Network error
- [ ] Server error
- [ ] Permission denied
- [ ] Session expired
- [ ] Offline

### 7.4 Notifications
- [ ] Toast (success, error, info)
- [ ] In-app banner
- [ ] Email (via Brevo)
- [ ] Push (native)

---

## Phase 8 — Design Tools

| Tool | Purpose |
|---|---|
| **Figma** | Mockup + Design system |
| **Storybook** | Component library |
| **Playwright** | UI E2E tests |
| **Lighthouse** | Performance + A11y |

---

## UI Priority Order
Backend Priority 0
↓
UI Phase 1 (Foundation)
↓
UI Phase 2 (Core Pages)
↓
UI Phase 3 (Advanced)
↓
UI Phase 4 (Design System Polish)
↓
UI Phase 5 (Responsive)
↓
UI Phase 6 (Accessibility)
↓
UI Phase 7 (UX Polish)
↓
UI Phase 8 (Tools + Testing)

text

---

## Non-Negotiable UI Rules

1. No marketing layout — private workspace feel
2. No excessive gradients or neon
3. No decorative AI imagery
4. Minimal animation
5. Editorial typography
6. Thin borders, layered surfaces
7. Calm, professional, cinematic
8. Mobile-first for capture
9. Desktop-first for review
10. Accessibility always

---

## Change Log

| Date | Change |
|---|---|
| 2026-10-06 | Initial file created |
