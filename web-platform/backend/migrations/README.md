# Cognix-Nexus Database Migration Architecture

Cognix-Nexus uses an ordered SQL migration pipeline applied automatically during startup via `persistence.py` -> `ensure_schema()`.

## Directory Structure
* `migrations/`: Contains numbered migrations (`001_initial.sql` through `040_phase20_21_release_evidence_runtime.sql`).

## Execution
* Migrations run idempotently against PostgreSQL (`options="-c search_path=public,extensions"`).
* New schema changes should be added as `041_<name>.sql` and referenced in `ensure_schema()` in `app/persistence.py`.
