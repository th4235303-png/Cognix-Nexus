from __future__ import annotations

"""Database-backed Book Intelligence acceptance contract.

The contract is safe to run against a test or staging database. It performs
read-only schema/lifecycle checks by default. Use --synthetic to create and
clean up a tiny owner-scoped fixture for duplicate/progress/provenance checks.
It never calls an LLM and never claims the 170-file corpus was processed.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

# Support direct execution from the backend working directory and CI runners.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from psycopg.errors import UniqueViolation

from app.store import store


REQUIRED_TABLES = {
    "books",
    "chapters",
    "chunks",
    "book_reading_progress",
    "reading_events",
    "chapter_summaries",
    "book_summaries",
    "summary_sources",
    "knowledge_items",
    "lesson_packs",
    "derived_books",
}


def db():
    if store.database is None:
        raise RuntimeError("DATABASE_URL is required for Book Intelligence acceptance")
    store.initialize()
    return store.database


def table_names(database) -> set[str]:
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE'"
            )
            return {row["table_name"] for row in cur.fetchall()}


def column_names(database, table: str) -> set[str]:
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (table,),
            )
            return {row["column_name"] for row in cur.fetchall()}


def run(synthetic: bool) -> dict:
    database = db()
    tables = table_names(database)
    missing_tables = sorted(REQUIRED_TABLES - tables)
    result = {
        "status": "PASS" if not missing_tables else "FAIL",
        "required_tables": sorted(REQUIRED_TABLES),
        "missing_tables": missing_tables,
        "synthetic": synthetic,
        "corpus_claim": "not executed; 9-category / 170-file corpus requires real corpus input",
    }
    if missing_tables or not synthetic:
        return result

    owner = "BOOK-ACCEPT-" + uuid4().hex[:10]
    book_id = "BOOK-ACCEPT-" + uuid4().hex[:10]
    duplicate_id = "BOOK-ACCEPT-DUP-" + uuid4().hex[:10]
    try:
        required_book_columns = {"id", "title", "status", "content_hash", "owner_id", "processing_stage"}
        result["books_columns_ok"] = required_book_columns <= column_names(database, "books")
        required_progress_columns = {"book_id", "owner_id", "status", "percent", "completed_units", "total_units"}
        result["progress_columns_ok"] = required_progress_columns <= column_names(database, "book_reading_progress")
        required_knowledge_columns = {"id", "book_id", "owner_id", "status", "source_chunk_ids"}
        result["knowledge_lineage_columns_ok"] = required_knowledge_columns <= column_names(database, "knowledge_items")
        if not all(result[k] for k in ("books_columns_ok", "progress_columns_ok", "knowledge_lineage_columns_ok")):
            result["status"] = "FAIL"
            return result

        with database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books(
                       id,title,language,file_type,source_kind,status,content_hash,
                       created_at,updated_at,owner_id,processing_stage
                    ) VALUES(%s,'Acceptance fixture','en','text','acceptance','queued',%s,now(),now(),%s,'queued')""",
                    (book_id, "fixture-hash-" + book_id, owner),
                )
                cur.execute("SAVEPOINT duplicate_fingerprint_check")
                try:
                    cur.execute(
                        """INSERT INTO books(
                           id,title,language,file_type,source_kind,status,content_hash,
                           created_at,updated_at,owner_id,processing_stage
                        ) VALUES(%s,'Duplicate fixture','en','text','acceptance','queued',%s,now(),now(),%s,'queued')""",
                        (duplicate_id, "fixture-hash-" + book_id, owner),
                    )
                except UniqueViolation:
                    cur.execute("ROLLBACK TO SAVEPOINT duplicate_fingerprint_check")
                    result["duplicate_fingerprint_rejected"] = True
                else:
                    cur.execute("ROLLBACK TO SAVEPOINT duplicate_fingerprint_check")
                    result["duplicate_fingerprint_rejected"] = False
                cur.execute("RELEASE SAVEPOINT duplicate_fingerprint_check")
                cur.execute(
                    """INSERT INTO book_reading_progress(
                       book_id,owner_id,status,percent,completed_units,total_units
                    ) VALUES(%s,%s,'queued',0,0,2)""",
                    (book_id, owner),
                )
            conn.commit()

        with database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT count(*) AS n FROM books WHERE owner_id=%s AND content_hash=%s",
                    (owner, "fixture-hash-" + book_id),
                )
                result["duplicate_fingerprint_visible"] = int(cur.fetchone()["n"]) == 1
                cur.execute(
                    "SELECT status,percent,completed_units,total_units FROM book_reading_progress WHERE book_id=%s AND owner_id=%s",
                    (book_id, owner),
                )
                progress = cur.fetchone()
                result["checkpoint_shape_ok"] = bool(
                    progress
                    and progress["status"] == "queued"
                    and progress["percent"] == 0
                    and progress["completed_units"] == 0
                    and progress["total_units"] == 2
                )

        result["status"] = "PASS" if all(
            result.get(k, False) for k in ("duplicate_fingerprint_visible", "duplicate_fingerprint_rejected", "checkpoint_shape_ok")
        ) else "FAIL"
        return result
    finally:
        with database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM book_reading_progress WHERE book_id=%s AND owner_id=%s", (book_id, owner))
                cur.execute("DELETE FROM books WHERE id IN (%s,%s) AND owner_id=%s", (book_id, duplicate_id, owner))
            conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args.synthetic)
    except Exception as exc:
        result = {"status": "ERROR", "error_type": type(exc).__name__}
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
