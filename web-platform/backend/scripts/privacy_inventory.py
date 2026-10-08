from __future__ import annotations

"""Read-only owner-data inventory for the final GDPR export/delete drill."""

import argparse
import json
from app.store import store


def run(owner_id: str) -> dict:
    if not owner_id.strip():
        raise ValueError("owner_id is required")
    if store.database is None:
        raise RuntimeError("DATABASE_URL is required")
    store.initialize()
    database = store.database
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT table_name
                   FROM information_schema.columns
                   WHERE table_schema='public' AND column_name='owner_id'
                   ORDER BY table_name"""
            )
            tables = [row["table_name"] for row in cur.fetchall()]
            counts = {}
            for table in tables:
                cur.execute(f'SELECT count(*) AS n FROM "{table}" WHERE owner_id=%s', (owner_id,))
                counts[table] = int(cur.fetchone()["n"])
    return {"status": "READY_FOR_OPERATOR_DRILL", "owner_id": owner_id, "tables": counts, "destructive_action_performed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-id", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.owner_id), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
