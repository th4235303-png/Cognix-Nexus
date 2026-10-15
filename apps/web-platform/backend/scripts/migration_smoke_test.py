from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo


BACKEND = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND / "migrations"
SMOKE_DB = "cognix_migration_smoke"


def main() -> int:
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        print("DATABASE_URL is required for the isolated migration smoke test", file=sys.stderr)
        return 2

    options = conninfo_to_dict(dsn)
    host = options.get("host", "localhost")
    database = options.get("dbname", options.get("database", ""))
    if host not in {"localhost", "127.0.0.1", "::1"} or database != "cognix_test":
        print(
            "Refusing to run migrations unless DATABASE_URL points to the local CI "
            "database named cognix_test.",
            file=sys.stderr,
        )
        return 2

    persistence = (BACKEND / "app" / "persistence.py").read_text(encoding="utf-8")
    start = persistence.index("migration_names = (")
    end = persistence.index(")\n        with self.connect", start)
    migration_names = re.findall(r'"(\d{3}_[^"]+\.sql)"', persistence[start:end])
    if not migration_names:
        print("Could not discover the runtime migration list", file=sys.stderr)
        return 2

    admin_dsn = make_conninfo(dsn, dbname="postgres")
    smoke_dsn = make_conninfo(dsn, dbname=SMOKE_DB)
    try:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            with admin.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {SMOKE_DB} WITH (FORCE)")
                cur.execute(f"CREATE DATABASE {SMOKE_DB}")
                for role in ("anon", "authenticated"):
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
                    if cur.fetchone() is None:
                        cur.execute(f"CREATE ROLE {role} NOLOGIN")

        with psycopg.connect(smoke_dsn) as conn:
            for name in migration_names:
                path = MIGRATIONS / name
                if not path.is_file():
                    raise RuntimeError(f"Registered migration file is missing: {name}")
                with conn.cursor() as cur:
                    cur.execute(path.read_text(encoding="utf-8"))
                conn.commit()
                print(f"PASS {name}")
        print(f"Applied {len(migration_names)} registered migrations to isolated database {SMOKE_DB}.")
        return 0
    except Exception as exc:
        print(f"Migration smoke test failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            with psycopg.connect(admin_dsn, autocommit=True) as admin:
                with admin.cursor() as cur:
                    cur.execute(f"DROP DATABASE IF EXISTS {SMOKE_DB} WITH (FORCE)")
        except Exception as cleanup_error:
            print(f"Warning: could not remove isolated smoke database: {cleanup_error}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
