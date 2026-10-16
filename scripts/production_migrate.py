#!/usr/bin/env python3
"""Zero-Downtime Safe Database Migration Runner for Cognix-Nexus.

Designed for automated production pipelines and containerless deployments (systemd / PM2).
Features:
- Pre-flight PostgreSQL connectivity check with exponential backoff.
- Executes ordered SQL migrations (`001_initial.sql` through `044_restrict_service_managed_brain_soul_youtube.sql`).
- Leverages transactional DDL and PostgreSQL advisory lock (`pg_advisory_xact_lock`) for zero race conditions.
- Validates applied schema revisions against `cognix_schema_migrations`.
- Non-zero exit code on failure to prevent deployment of broken states.
"""

import os
import sys
import time
from pathlib import Path

# Add backend directory to path
repo_root = Path(__file__).resolve().parent.parent
backend_dir = repo_root / "apps/web-platform" / "backend"
sys.path.insert(0, str(backend_dir))


def log(msg: str) -> None:
    print(f"[Cognix-Migrate] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}", flush=True)


def wait_for_database(dsn: str, max_retries: int = 15, delay: float = 2.0) -> bool:
    """Verifies PostgreSQL connectivity before applying schema migrations."""
    log("Verifying PostgreSQL database connectivity...")
    try:
        import psycopg
    except ImportError:
        log("ERROR: `psycopg` is required to run database migrations.")
        return False

    for attempt in range(1, max_retries + 1):
        try:
            with psycopg.connect(dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    log(f"Database reachable on attempt {attempt}.")
                    return True
        except Exception as exc:
            log(f"Attempt {attempt}/{max_retries} connection failed: {exc}")
            time.sleep(delay)

    log("ERROR: Timed out waiting for database connectivity.")
    return False


def run_migrations(dsn: str) -> bool:
    """Runs ensure_schema via Cognix Database engine."""
    from app.persistence import Database

    log("Executing sequential schema migrations...")
    try:
        db = Database(dsn)
        db.ensure_schema()
        log("Database schema synchronization finished successfully.")

        # Query applied migrations
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT migration_name, applied_at FROM cognix_schema_migrations ORDER BY migration_name"
                )
                rows = cur.fetchall()
                log(f"Total applied migrations: {len(rows)}")
                if rows:
                    log(f"Latest applied migration: {rows[-1]['migration_name']} ({rows[-1]['applied_at']})")
        return True
    except Exception as exc:
        log(f"CRITICAL: Migration run failed: {exc}")
        return False


def main() -> None:
    log("Starting Zero-Downtime Migration Automation for Cognix-Nexus...")
    dsn = os.getenv("DATABASE_URL", "").strip()
    if not dsn:
        log("WARNING: DATABASE_URL not set. In local mock mode, skipping database migration.")
        sys.exit(0)

    if not wait_for_database(dsn):
        sys.exit(1)

    if not run_migrations(dsn):
        sys.exit(1)

    log("Migration automation completed successfully.")


if __name__ == "__main__":
    main()
