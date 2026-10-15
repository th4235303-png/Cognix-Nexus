# Cognix-Nexus — Repository Structure

> Generated from the recursive Git tree of `main` for `th4235303-png/Cognix-Nexus`.
>
> This document is a **repository tree / structure manifest**, not a conceptual architecture diagram. It records the paths that are actually present in the repository, including archived files, deployment configuration, backend/frontend source, migrations, tests, and compiled `__pycache__` artifacts.
>
> **Source ref:** `main`  
> **Repository tree SHA:** `e5520fc7a6e4dd1596585e5066c649c2737ba09a`  
> **Generated:** 2026-10-15

## Full tree

```text
Cognix-Nexus/
├── .env.example
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       ├── codeql.yml
│       └── release-gates.yml
├── .gitignore
├── CURRENT_STATE.md
├── PROJECT_OVERVIEW.md
├── README.md
├── ROADMAP.md
├── SECURITY.md
├── TOOL.md
├── UI_DESIGN_SYSTEM.md
├── archive/
│   └── legacy/
│       ├── root/
│       │   ├── AGENT.md
│       │   ├── ARCHITECTURE.md
│       │   ├── DATA_MODEL.md
│       │   ├── DECISIONS.md
│       │   ├── DEPLOYMENT.md
│       │   ├── PIPELINE.md
│       │   ├── PRODUCTION_E2E_STATUS.md
│       │   ├── PRODUCTION_STATUS.md
│       │   ├── REMAINING_WORK.md
│       │   ├── TOOLS.md
│       │   ├── TROUBLESHOOTING.md
│       │   ├── UI_PLAN.md
│       │   └── UI_STATUS.md
│       └── web-platform/
│           └── docs/
│               ├── book-intelligence-product-spec.md
│               ├── brain-vault-roadmap.md
│               ├── brain-vault.md
│               ├── completion-contract.md
│               ├── executable-workflow-audit.md
│               ├── external-activation-checklist.md
│               ├── master-plan-v2.md
│               ├── operations.md
│               ├── phase-14-18.md
│               └── production-integrations.md
├── backend -> (symlink)
├── docs/
│   ├── AGENT.md
│   ├── AI_RAG.md
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── DATABASE.md
│   ├── DATA_MODEL.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   ├── EVALUATION_DATASETS.md
│   ├── FUTURE_PHASE_FOUNDATIONS.md
│   ├── MASTER_PLAN_SCOPE_MATRIX.md
│   ├── MEDIA_INTELLIGENCE_SOURCE_MONITORING_PLAN.md
│   ├── OPERATIONS.md
│   ├── PHASE_13_17_PREPARATION_PLAN.md
│   ├── PHASE_13_FOUNDATION.md
│   ├── PHASE_14_FOUNDATION.md
│   ├── PHASE_15_FOUNDATION.md
│   ├── PHASE_16_FOUNDATION.md
│   ├── PHASE_17_FOUNDATION.md
│   ├── PHASE_18_19_PREPARATION_PLAN.md
│   ├── PHASE_18_FOUNDATION.md
│   ├── PHASE_19_FOUNDATION.md
│   ├── PHASE_20_21_PREPARATION_PLAN.md
│   ├── PHASE_20_FOUNDATION.md
│   ├── PHASE_21_FOUNDATION.md
│   ├── PHASE_ACTIVATION_MANIFEST.json
│   ├── PHASE_ACTIVATION_MATRIX.md
│   ├── PIPELINE.md
│   ├── PROMPTS.md
│   ├── RELEASE_GATES.md
│   ├── REPOSITORY_STRUCTURE.md
│   ├── STORAGE.md
│   ├── TELEGRAM_INTEGRATION.md
│   ├── TESTING.md
│   ├── TROUBLESHOOTING.md
│   ├── USER_GUIDE.md
│   ├── eval-fixtures/
│   │   ├── agent.json
│   │   ├── ai.json
│   │   ├── learning.json
│   │   ├── performance.json
│   │   └── security.json
│   ├── features/
│   │   └── book-intelligence.md
│   ├── master_result all
│   └── runbooks/
│       └── external-activation.md
├── mobile/
│   ├── .env.example
│   ├── App.tsx
│   ├── README.md
│   ├── app.json
│   ├── eas.json
│   └── package.json
├── netlify.toml
├── render.yaml
└── web-platform/
    ├── backend/
    │   ├── .env.example
    │   ├── PROVIDER_FREE_TIER_SETUP.md
    │   ├── README.md
    │   ├── app/
    │   │   ├── __pycache__/
    │   │   │   ├── persistence.cpython-314.pyc
    │   │   │   ├── request_context.cpython-314.pyc
    │   │   │   └── store.cpython-314.pyc
    │   │   ├── auth.py
    │   │   ├── main.py
    │   │   ├── ownership.py
    │   │   ├── persistence.py
    │   │   ├── request_context.py
    │   │   ├── routers/
    │   │   │   ├── __init__.py
    │   │   │   ├── __pycache__/
    │   │   │   │   └── brain_agent.cpython-314.pyc
    │   │   │   ├── activity.py
    │   │   │   ├── advanced_layer.py
    │   │   │   ├── book_intelligence.py
    │   │   │   ├── brain_advanced.py
    │   │   │   ├── brain_agent.py
    │   │   │   ├── brain_documents.py
    │   │   │   ├── brain_media.py
    │   │   │   ├── brain_vault.py
    │   │   │   ├── core_integration.py
    │   │   │   ├── exports.py
    │   │   │   ├── integrations.py
    │   │   │   ├── intelligence.py
    │   │   │   ├── learning_science.py
    │   │   │   ├── level_up.py
    │   │   │   ├── life_integration.py
    │   │   │   ├── media_boundary.py
    │   │   │   ├── processing.py
    │   │   │   ├── release_evidence.py
    │   │   │   ├── reviews.py
    │   │   │   ├── sources.py
    │   │   │   ├── telegram.py
    │   │   │   └── usage.py
    │   │   ├── services/
    │   │   │   ├── __init__.py
    │   │   │   ├── __pycache__/
    │   │   │   │   ├── __init__.cpython-314.pyc
    │   │   │   │   ├── agent.cpython-314.pyc
    │   │   │   │   └── llm.cpython-314.pyc
    │   │   │   ├── active_layer/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── __pycache__/
    │   │   │   │   │   ├── __init__.cpython-314.pyc
    │   │   │   │   │   ├── contracts.cpython-314.pyc
    │   │   │   │   │   ├── events.cpython-314.pyc
    │   │   │   │   │   ├── execution.cpython-314.pyc
    │   │   │   │   │   └── validation.cpython-314.pyc
    │   │   │   │   ├── contracts.py
    │   │   │   │   ├── events.py
    │   │   │   │   ├── execution.py
    │   │   │   │   └── validation.py
    │   │   │   ├── advanced_layer/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   └── vault.py
    │   │   │   ├── advanced_layer_service.py
    │   │   │   ├── agent.py
    │   │   │   ├── ai_usage_tracker.py
    │   │   │   ├── book_ingestion.py
    │   │   │   ├── book_intelligence.py
    │   │   │   ├── book_processing.py
    │   │   │   ├── book_storage.py
    │   │   │   ├── core_integration/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   ├── document_assistant.py
    │   │   │   │   └── language_tutor.py
    │   │   │   ├── core_integration_service.py
    │   │   │   ├── document_ocr.py
    │   │   │   ├── embeddings.py
    │   │   │   ├── export_worker.py
    │   │   │   ├── google_drive.py
    │   │   │   ├── google_drive_package.py
    │   │   │   ├── learning_science/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   └── planning.py
    │   │   │   ├── learning_science_service.py
    │   │   │   ├── lease_runner.py
    │   │   │   ├── level_up.py
    │   │   │   ├── life_integration/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   └── restore.py
    │   │   │   ├── life_integration_service.py
    │   │   │   ├── llm.py
    │   │   │   ├── media_boundary/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   ├── media_processing.py
    │   │   │   │   ├── metadata.py
    │   │   │   │   └── native_capabilities.py
    │   │   │   ├── media_boundary_service.py
    │   │   │   ├── object_storage.py
    │   │   │   ├── processing.py
    │   │   │   ├── release_evidence/
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── checklist.py
    │   │   │   │   ├── contracts.py
    │   │   │   │   └── operations.py
    │   │   │   ├── release_evidence_service.py
    │   │   │   ├── research_processor.py
    │   │   │   ├── ssrf.py
    │   │   │   ├── task_retry.py
    │   │   │   ├── telegram.py
    │   │   │   ├── trust.py
    │   │   │   └── upload_limits.py
    │   │   ├── store.py
    │   │   └── worker.py
    │   ├── migrations/
    │   │   ├── 001_initial.sql
    │   │   ├── 002_api_contract_alignment.sql
    │   │   ├── 003_persistence_hardening.sql
    │   │   ├── 004_brain_vault_foundation.sql
    │   │   ├── 005_brain_vault_search.sql
    │   │   ├── 006_brain_vault_advanced.sql
    │   │   ├── 007_book_storage.sql
    │   │   ├── 008_document_and_synthesis_hardening.sql
    │   │   ├── 009_media_assets.sql
    │   │   ├── 010_agent_active_layer.sql
    │   │   ├── 010_intelligence_life_reliability.sql
    │   │   ├── 011_level_up20_completion.sql
    │   │   ├── 012_storage_reliability.sql
    │   │   ├── 013_workflow_fk_indexes.sql
    │   │   ├── 014_move_vector_extension.sql
    │   │   ├── 015_supabase_storage_bucket.sql
    │   │   ├── 016_processing_idempotency.sql
    │   │   ├── 017_lock_down_data_api_roles.sql
    │   │   ├── 018_book_processing_pipeline.sql
    │   │   ├── 019_processing_task_claims.sql
    │   │   ├── 020_record_ownership.sql
    │   │   ├── 021_brain_record_ownership.sql
    │   │   ├── 022_vault_item_ownership.sql
    │   │   ├── 023_concepts_owner_unique.sql
    │   │   ├── 024_book_export_job_leases.sql
    │   │   ├── 025_rls_owner_isolation.sql
    │   │   ├── 026_level_up_owner_isolation.sql
    │   │   ├── 027_rls_helper_performance.sql
    │   │   ├── 028_rls_policy_dedup.sql
    │   │   ├── 029_latest_action_wins.sql
    │   │   ├── 030_processing_task_superseded_index.sql
    │   │   ├── 031_book_intelligence.sql
    │   │   ├── 032_phase7_12_hardening.sql
    │   │   ├── 033_rls_policy_initplan_indexes.sql
    │   │   ├── 034_phase13_active_layer_runtime.sql
    │   │   ├── 035_phase14_learning_science_runtime.sql
    │   │   ├── 036_phase15_life_integration_runtime.sql
    │   │   ├── 037_phase16_advanced_layer_runtime.sql
    │   │   ├── 038_phase17_core_integration_runtime.sql
    │   │   ├── 039_phase18_19_media_boundary_runtime.sql
    │   │   ├── 040_phase20_21_release_evidence_runtime.sql
    │   │   ├── 041_phase22_book_acceptance_schema.sql
    │   │   └── README.md
    │   ├── requirements.lock
    │   ├── requirements.txt
    │   ├── scripts/
    │   │   ├── backup_restore_drill.py
    │   │   ├── book_acceptance_contract.py
    │   │   ├── lighthouse_check.py
    │   │   ├── migration_smoke_test.py
    │   │   ├── privacy_inventory.py
    │   │   ├── provider_e2e.py
    │   │   ├── release_gate_preflight.py
    │   │   ├── render_health_check.py
    │   │   └── sentry_live_check.py
    │   └── tests/
    │       ├── __pycache__/
    │       │   └── test_phase13_runtime.cpython-314-pytest-9.1.1.pyc
    │       ├── test_active_layer_events.py
    │       ├── test_active_layer_validation.py
    │       ├── test_api.py
    │       ├── test_b2_region_inference.py
    │       ├── test_book_intelligence.py
    │       ├── test_book_intelligence_migration.py
    │       ├── test_concept_owner_uniqueness_migration.py
    │       ├── test_core_integration_contracts.py
    │       ├── test_database_integration.py
    │       ├── test_future_foundations.py
    │       ├── test_level_up20.py
    │       ├── test_media_boundary_contracts.py
    │       ├── test_migration_security_contract.py
    │       ├── test_multi_provider_routing.py
    │       ├── test_persistence_ownership.py
    │       ├── test_phase13_21_prepared_contracts.py
    │       ├── test_phase13_runtime.py
    │       ├── test_phase14_learning_contracts.py
    │       ├── test_phase14_learning_science.py
    │       ├── test_phase15_life_integration.py
    │       ├── test_phase15_life_integration_contracts.py
    │       ├── test_phase16_advanced_contracts.py
    │       ├── test_phase16_advanced_layer.py
    │       ├── test_phase17_core_integration.py
    │       ├── test_phase18_19_media_boundary.py
    │       ├── test_phase20_21_release_evidence.py
    │       ├── test_provider_e2e_gate_classification.py
    │       ├── test_release_evidence_contracts.py
    │       ├── test_release_gate_preflight.py
    │       ├── test_research_processor.py
    │       ├── test_retrieval_ownership_contract.py
    │       ├── test_rls_owner_isolation_migration.py
    │       ├── test_security_hardening.py
    │       ├── test_ssrf.py
    │       ├── test_storage.py
    │       ├── test_stress_workflows.py
    │       ├── test_upload_limits.py
    │       └── test_worker_reliability.py
    └── frontend/
        ├── .env.example
        ├── .eslintrc.json
        ├── app/
        │   ├── activity/
        │   │   └── page.tsx
        │   ├── approved/
        │   │   └── page.tsx
        │   ├── books/
        │   │   ├── [id]/
        │   │   │   └── page.tsx
        │   │   └── page.tsx
        │   ├── chat/
        │   │   └── page.tsx
        │   ├── collections/
        │   │   └── page.tsx
        │   ├── dashboard/
        │   │   └── page.tsx
        │   ├── delivery/
        │   │   └── page.tsx
        │   ├── documents/
        │   │   └── page.tsx
        │   ├── export/
        │   │   └── page.tsx
        │   ├── forgot-password/
        │   │   └── page.tsx
        │   ├── globals.css
        │   ├── graph/
        │   │   └── page.tsx
        │   ├── knowledge/
        │   │   └── page.tsx
        │   ├── layout.tsx
        │   ├── lens/
        │   │   └── page.tsx
        │   ├── level-up/
        │   │   └── page.tsx
        │   ├── login/
        │   │   └── page.tsx
        │   ├── notes/
        │   │   └── page.tsx
        │   ├── page.tsx
        │   ├── processing/
        │   │   └── page.tsx
        │   ├── review/
        │   │   └── page.tsx
        │   ├── settings/
        │   │   └── page.tsx
        │   ├── sources/
        │   │   ├── [id]/
        │   │   │   └── page.tsx
        │   │   ├── add/
        │   │   │   └── page.tsx
        │   │   ├── all/
        │   │   │   └── page.tsx
        │   │   └── inbox/
        │   │       └── page.tsx
        │   ├── tags/
        │   │   └── page.tsx
        │   ├── tutor/
        │   │   └── page.tsx
        │   ├── usage/
        │   │   └── page.tsx
        │   └── vault/
        │       └── page.tsx
        ├── components.json
        ├── components/
        │   ├── layout/
        │   │   ├── app-shell.tsx
        │   │   ├── header.tsx
        │   │   └── sidebar.tsx
        │   ├── research/
        │   │   └── workspace-ui.tsx
        │   ├── shared/
        │   │   ├── cognix-primitives.tsx
        │   │   └── status-badges.tsx
        │   └── ui/
        │       ├── accordion.tsx
        │       ├── alert-dialog.tsx
        │       ├── alert.tsx
        │       ├── aspect-ratio.tsx
        │       ├── avatar.tsx
        │       ├── badge.tsx
        │       ├── breadcrumb.tsx
        │       ├── button.tsx
        │       ├── calendar.tsx
        │       ├── card.tsx
        │       ├── carousel.tsx
        │       ├── chart.tsx
        │       ├── checkbox.tsx
        │       ├── collapsible.tsx
        │       ├── command.tsx
        │       ├── context-menu.tsx
        │       ├── dialog.tsx
        │       ├── drawer.tsx
        │       ├── dropdown-menu.tsx
        │       ├── form.tsx
        │       ├── hover-card.tsx
        │       ├── input-otp.tsx
        │       ├── input.tsx
        │       ├── label.tsx
        │       ├── menubar.tsx
        │       ├── navigation-menu.tsx
        │       ├── pagination.tsx
        │       ├── popover.tsx
        │       ├── progress.tsx
        │       ├── radio-group.tsx
        │       ├── resizable.tsx
        │       ├── scroll-area.tsx
        │       ├── select.tsx
        │       ├── separator.tsx
        │       ├── sheet.tsx
        │       ├── skeleton.tsx
        │       ├── slider.tsx
        │       ├── sonner.tsx
        │       ├── switch.tsx
        │       ├── table.tsx
        │       ├── tabs.tsx
        │       ├── textarea.tsx
        │       ├── toast.tsx
        │       ├── toaster.tsx
        │       ├── toggle-group.tsx
        │       ├── toggle.tsx
        │       └── tooltip.tsx
        ├── e2e/
        │   ├── accessibility.spec.ts
        │   └── authenticated-smoke.spec.ts
        ├── hooks/
        │   └── use-toast.ts
        ├── lib/
        │   ├── api.ts
        │   ├── researchData.ts
        │   ├── supabase.ts
        │   ├── types/
        │   │   └── source.ts
        │   └── utils.ts
        ├── next.config.js
        ├── package-lock.json
        ├── package.json
        ├── playwright.config.ts
        ├── postcss.config.js
        ├── tailwind.config.ts
        └── tsconfig.json
```

## Structure notes

### Root-level layout

The repository is organized as a multi-surface project with:

- root-level project documentation and policy files;
- GitHub automation under `.github/`;
- an archived legacy implementation under `archive/legacy/`;
- a documentation hub under `docs/`;
- a mobile application under `mobile/`;
- deployment configuration for Netlify and Render;
- the active web platform under `web-platform/`;
- a `backend` symbolic link at repository root.

### Active web platform

`web-platform/` is split into:

- `backend/` — Python application, routers, service layer, database migrations, operational scripts, and backend tests.
- `frontend/` — Next.js application routes, shared/layout components, UI primitives, hooks, API helpers, types, and Playwright E2E tests.

### Backend service organization

The backend service layer contains both general services and phase-oriented domain modules, including:

- active-layer runtime;
- advanced layer;
- book ingestion, intelligence, processing, and storage;
- core integration;
- learning science;
- life integration;
- media boundary;
- release evidence;
- LLM, embeddings, OCR, storage, research processing, retry, trust, Telegram, and provider-related infrastructure.

### Database migrations

`web-platform/backend/migrations/` contains the numbered SQL migration history through migration `041_phase22_book_acceptance_schema.sql`, plus the migration README. The tree also contains two `010_*` migrations with distinct names; both are recorded exactly as present.

### Generated / compiled artifacts

The repository tree currently contains Python bytecode under several `__pycache__/` directories. These entries are intentionally represented in this snapshot because this document describes the **actual Git tree**, rather than an idealized source-only tree.

### Symlink

The root-level `backend` entry is recorded by Git as a symbolic link (`mode 120000`). The recursive tree reports it as a blob with the link target represented separately from the normal directory tree.

## Accuracy boundary

This document is intended to be a faithful **path-level snapshot** of the `main` branch tree at the generation date above. It does not infer files that are absent from Git, does not expand ignored/untracked local files, and does not replace the actual repository tree with a conceptual architecture.
