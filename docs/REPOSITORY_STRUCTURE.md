# Repository Structure — Cognix Nexus

This document is the canonical current layout for active tracked code. It replaces the older full-tree inventory, which described pre-reorganization paths and generated cache artifacts.

```text
Cognix-Nexus/
├── apps/
│   ├── mobile/                         # Reserved mobile product surface
│   └── web-platform/
│       ├── frontend/                   # Next.js / React / TypeScript web application
│       └── backend/                    # FastAPI API, worker, migrations and backend tests
├── docs/                               # Current architecture, data, operations and release docs
├── scripts/                            # Maintenance, migration and verification tooling
├── .github/workflows/                  # CI, security and deployment automation
└── archive/legacy/                     # Historical material; not active runtime code
```

## Placement rules

- Keep browser code in `apps/web-platform/frontend/` and API/worker/database code in `apps/web-platform/backend/`.
- `apps/mobile/` reserves the future native/mobile product boundary. Its presence does not claim a production mobile release.
- Keep project-wide README, policy, status and roadmap Markdown files at repository root; keep detailed current guides in `docs/`.
- Python bytecode, local runtime output and dependencies are generated artifacts and are not repository source.
- `archive/legacy/` is reference material only and must not be treated as the current implementation.

Use `../CURRENT_STATE.md` for release evidence and `../ROADMAP.md` for the planned product sequence.
