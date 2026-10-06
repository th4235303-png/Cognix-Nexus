from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.request_context import current_request_owner


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.worker_id = os.getenv("COGNIX_WORKER_ID") or f"worker-{os.getpid()}"
        self._claim_tokens: dict[str, str] = {}
        self._pool = ConnectionPool(
            conninfo=self.dsn,
            min_size=max(1, int(os.getenv("COGNIX_DB_POOL_MIN", "1"))),
            max_size=max(1, int(os.getenv("COGNIX_DB_POOL_MAX", "10"))),
            kwargs={"row_factory": dict_row, "options": "-c search_path=public,extensions"},
            open=False,
        )
        self._pool.open(wait=True)

    def claim_task(self, task_id: str) -> str | None:
        """Atomically lease a runnable task and return its unique fencing token."""
        claim_token = f"{self.worker_id}:{uuid4().hex}"
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE processing_tasks
                       SET claimed_by=%s, claimed_at=now()
                       WHERE id=%s
                         AND status IN ('queued', 'running')
                         AND stage NOT IN ('needs_review', 'approved')
                         AND (
                           status <> 'queued' OR retry_count=0 OR updated_at <= now() - make_interval(
                             secs => LEAST(300.0, 5.0 * power(2.0, LEAST(GREATEST(retry_count - 1, 0), 6)))::double precision
                           )
                         )
                         AND (claimed_by IS NULL OR claimed_at IS NULL
                              OR claimed_at < now() - interval '30 minutes')
                       RETURNING id""",
                    (claim_token, task_id),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            return None
        self._claim_tokens[task_id] = claim_token
        return claim_token

    def try_claim_task(self, task_id: str) -> bool:
        """Compatibility wrapper for callers that only need claim success."""
        return self.claim_task(task_id) is not None

    def renew_task_claim(self, task_id: str, claim_token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE processing_tasks
                       SET claimed_at=now()
                       WHERE id=%s AND claimed_by=%s
                         AND claimed_at >= now() - interval '30 minutes'
                         AND status IN ('queued', 'running')
                         AND stage NOT IN ('needs_review', 'approved')
                       RETURNING id""",
                    (task_id, claim_token),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def cancel_processing_task(
        self,
        task_id: str,
        reason: str,
        superseded_by: str | None = None,
    ) -> bool:
        """Cooperatively cancel a queued/running task; its lease is fenced immediately."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE processing_tasks
                       SET status='cancelled', error=%s, superseded_by=%s,
                           claimed_by=NULL, claimed_at=NULL, updated_at=now()
                       WHERE id=%s AND status IN ('queued','running')
                       RETURNING id""",
                    (reason, superseded_by, task_id),
                )
                row = cur.fetchone()
            conn.commit()
        self._claim_tokens.pop(task_id, None)
        return row is not None

    def release_task(self, task_id: str, claim_token: str | None = None) -> bool:
        token = claim_token or self._claim_tokens.get(task_id)
        if token is None:
            return False
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE processing_tasks SET claimed_by=NULL, claimed_at=NULL
                       WHERE id=%s AND claimed_by=%s
                         AND claimed_at >= now() - interval '30 minutes'
                       RETURNING id""",
                    (task_id, token),
                )
                row = cur.fetchone()
            conn.commit()
        if self._claim_tokens.get(task_id) == token:
            self._claim_tokens.pop(task_id, None)
        return row is not None

    def claim_book_processing(self, book_id: str) -> tuple[dict[str, Any], str] | None:
        token = uuid4().hex
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books
                       SET processing_claimed_by=%s, processing_claimed_at=now(),
                           processing_claim_token=%s, status='processing',
                           processing_stage='extracting',
                           processing_attempts=processing_attempts+1,
                           processing_error=NULL, processing_started_at=now(),
                           updated_at=now()
                       WHERE id=%s
                         AND source_kind='upload'
                         AND (binary_path IS NOT NULL OR binary_storage IS NOT NULL
                              OR original_filename IS NOT NULL)
                         AND processing_attempts < 3
                         AND (
                           status='queued'
                           OR (
                             status='failed'
                             AND updated_at <= now() - make_interval(
                               secs => LEAST(
                                 300.0,
                                 5.0 * power(2.0, LEAST(GREATEST(processing_attempts - 1, 0), 6))
                               )::double precision
                             )
                           )
                           OR (
                             status='processing' AND processing_stage='extracting'
                             AND (processing_started_at IS NULL
                                  OR processing_started_at < now() - interval '15 minutes')
                           )
                         )
                         AND (processing_claim_token IS NULL
                              OR processing_claimed_at IS NULL
                              OR processing_claimed_at < now() - interval '30 minutes')
                       RETURNING *""",
                    (self.worker_id, token, book_id),
                )
                row = cur.fetchone()
            conn.commit()
        return (row, token) if row is not None else None

    def renew_book_processing_claim(self, book_id: str, token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books SET processing_claimed_at=now()
                       WHERE id=%s AND processing_claim_token=%s
                         AND processing_claimed_by=%s
                         AND processing_claimed_at >= now() - interval '30 minutes'
                         AND status='processing' AND processing_stage='extracting'
                       RETURNING id""",
                    (book_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def fail_book_processing(self, book_id: str, token: str, error: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books
                       SET status='failed', processing_stage='failed',
                           processing_error=%s, updated_at=now(),
                           processing_claimed_by=NULL, processing_claimed_at=NULL,
                           processing_claim_token=NULL
                       WHERE id=%s AND processing_claim_token=%s
                         AND processing_claimed_by=%s
                         AND processing_claimed_at >= now() - interval '30 minutes'
                         AND status='processing' AND processing_stage='extracting'
                       RETURNING id""",
                    (error[:4000], book_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def complete_book_extraction(
        self,
        book_id: str,
        token: str,
        title: str,
        author: str | None,
        chapters: list[tuple],
        chunks: list[tuple],
    ) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books
                       SET title=%s, author=%s, status='processing',
                           processing_stage='embedding', processing_error=NULL,
                           processing_claimed_by=NULL, processing_claimed_at=NULL,
                           processing_claim_token=NULL, updated_at=now()
                       WHERE id=%s AND processing_claim_token=%s
                         AND processing_claimed_by=%s
                         AND processing_claimed_at >= now() - interval '30 minutes'
                         AND status='processing' AND processing_stage='extracting'
                       RETURNING id""",
                    (title, author, book_id, token, self.worker_id),
                )
                if cur.fetchone() is None:
                    return False
                cur.execute(
                    """DELETE FROM embeddings WHERE owner_type='chunk' AND owner_id IN
                       (SELECT c.id FROM chunks c JOIN chapters ch ON ch.id=c.chapter_id
                        WHERE ch.book_id=%s)""",
                    (book_id,),
                )
                cur.execute("DELETE FROM chunks WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id=%s)", (book_id,))
                cur.execute("DELETE FROM chapters WHERE book_id=%s", (book_id,))
                cur.executemany(
                    "INSERT INTO chapters(id,book_id,chapter_number,title,created_at) VALUES(%s,%s,%s,%s,%s)",
                    chapters,
                )
                cur.executemany(
                    """INSERT INTO chunks(
                           id,chapter_id,sequence,content,page_number,start_offset,end_offset,token_count,created_at
                       ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    chunks,
                )
            conn.commit()
        return True

    def claim_book_finalization(self, book_id: str) -> str | None:
        token = uuid4().hex
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books SET processing_claimed_by=%s,
                           processing_claimed_at=now(), processing_claim_token=%s
                       WHERE id=%s AND status='processing' AND processing_stage='embedding'
                         AND (processing_claim_token IS NULL OR processing_claimed_at IS NULL
                              OR processing_claimed_at < now() - interval '30 minutes')
                       RETURNING id""",
                    (self.worker_id, token, book_id),
                )
                row = cur.fetchone()
            conn.commit()
        return token if row is not None else None

    def complete_book_finalization(self, book_id: str, token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books
                       SET status='ready', processing_stage='completed', processed_at=now(),
                           processing_error=NULL, updated_at=now(),
                           processing_claimed_by=NULL, processing_claimed_at=NULL,
                           processing_claim_token=NULL
                       WHERE id=%s AND processing_claim_token=%s
                         AND processing_claimed_by=%s
                         AND processing_claimed_at >= now() - interval '30 minutes'
                         AND status='processing' AND processing_stage='embedding'
                         AND EXISTS (
                           SELECT 1 FROM chunks c JOIN chapters ch ON ch.id=c.chapter_id
                           WHERE ch.book_id=books.id
                         )
                         AND NOT EXISTS (
                           SELECT 1 FROM chunks c JOIN chapters ch ON ch.id=c.chapter_id
                           LEFT JOIN embeddings e ON e.owner_type='chunk' AND e.owner_id=c.id
                           WHERE ch.book_id=books.id AND e.owner_id IS NULL
                         )
                       RETURNING id""",
                    (book_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def release_book_claim(self, book_id: str, token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE books SET processing_claimed_by=NULL,
                           processing_claimed_at=NULL, processing_claim_token=NULL
                       WHERE id=%s AND processing_claim_token=%s
                         AND processing_claimed_by=%s
                         AND processing_claimed_at >= now() - interval '30 minutes'
                       RETURNING id""",
                    (book_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def claim_export_job(self, export_id: str) -> tuple[dict[str, Any], str] | None:
        token = uuid4().hex
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE export_jobs
                       SET claimed_by=%s, claimed_at=now(), claim_token=%s
                       WHERE id=%s AND status IN ('queued', 'uploading')
                         AND (claim_token IS NULL OR claimed_at IS NULL
                              OR claimed_at < now() - interval '30 minutes')
                       RETURNING *""",
                    (self.worker_id, token, export_id),
                )
                row = cur.fetchone()
            conn.commit()
        return (row, token) if row is not None else None

    def renew_export_job_claim(self, export_id: str, token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE export_jobs SET claimed_at=now()
                       WHERE id=%s AND claim_token=%s
                         AND claimed_by=%s
                         AND claimed_at >= now() - interval '30 minutes'
                         AND status='uploading'
                       RETURNING id""",
                    (export_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    def transition_export_job(
        self,
        export_id: str,
        token: str,
        expected_status: str,
        status: str,
        drive_reference: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE export_jobs
                       SET status=%s, drive_reference=%s, safe_reference=%s,
                           error=%s, updated_at=now()
                       WHERE id=%s AND claim_token=%s
                         AND claimed_by=%s
                         AND claimed_at >= now() - interval '30 minutes'
                         AND status=%s
                       RETURNING *""",
                    (
                        status, drive_reference, drive_reference, error,
                        export_id, token, self.worker_id, expected_status,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return self._export_row(row) if row is not None else None

    def release_export_job_claim(self, export_id: str, token: str) -> bool:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE export_jobs SET claimed_by=NULL, claimed_at=NULL, claim_token=NULL
                       WHERE id=%s AND claim_token=%s
                         AND claimed_by=%s
                         AND claimed_at >= now() - interval '30 minutes'
                         AND status IN ('queued','uploading')
                       RETURNING id""",
                    (export_id, token, self.worker_id),
                )
                row = cur.fetchone()
            conn.commit()
        return row is not None

    @contextmanager
    def connect(self):
        with self._pool.connection() as conn:
            owner_id = current_request_owner()
            if owner_id:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT set_config('request.jwt.claim.sub', %s, true)",
                        (owner_id,),
                    )
            yield conn

    def close(self) -> None:
        self._pool.close()

    def ping(self) -> bool:
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            return False

    def ensure_schema(self) -> None:
        migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
        migration_names = (
            "001_initial.sql",
            "002_api_contract_alignment.sql",
            "003_persistence_hardening.sql",
            "004_brain_vault_foundation.sql",
            "005_brain_vault_search.sql",
            "006_brain_vault_advanced.sql",
            "007_book_storage.sql",
            "008_document_and_synthesis_hardening.sql",
            "009_media_assets.sql",
            "010_agent_active_layer.sql",
            "010_intelligence_life_reliability.sql",
            "011_level_up20_completion.sql",
            "012_storage_reliability.sql",
            "013_workflow_fk_indexes.sql",
            "014_move_vector_extension.sql",
            "015_supabase_storage_bucket.sql",
            "016_processing_idempotency.sql",
            "017_lock_down_data_api_roles.sql",
            "018_book_processing_pipeline.sql",
            "019_processing_task_claims.sql",
            "020_record_ownership.sql",
            "021_brain_record_ownership.sql",
            "022_vault_item_ownership.sql",
            "023_concepts_owner_unique.sql",
            "024_book_export_job_leases.sql",
            "025_rls_owner_isolation.sql",
            "026_level_up_owner_isolation.sql",
            "027_rls_helper_performance.sql",
            "028_rls_policy_dedup.sql",
        )
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(7246823145061)")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cognix_schema_migrations (
                        migration_name TEXT PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cur.execute("SELECT to_regclass('public.sources') AS table_name")
                exists = cur.fetchone()["table_name"] is not None
                if not exists:
                    cur.execute((migrations_dir / "001_initial.sql").read_text())
                    cur.execute(
                        "INSERT INTO cognix_schema_migrations(migration_name) VALUES(%s) "
                        "ON CONFLICT (migration_name) DO NOTHING",
                        ("001_initial.sql",),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                          to_regclass('public.sources') AS sources,
                          to_regclass('public.processing_tasks') AS processing_tasks,
                          to_regclass('public.claims') AS claims,
                          to_regclass('public.reviews') AS reviews,
                          to_regclass('public.export_jobs') AS export_jobs,
                          to_regclass('public.activity_events') AS activity_events
                        """
                    )
                    missing = [
                        table_name
                        for table_name, relation in cur.fetchone().items()
                        if relation is None
                    ]
                    if missing:
                        raise RuntimeError(
                            "Existing database has an incomplete base schema; "
                            "refusing to skip migration 001. Missing tables: "
                            + ", ".join(missing)
                        )
                    cur.execute(
                        "INSERT INTO cognix_schema_migrations(migration_name) VALUES(%s) "
                        "ON CONFLICT (migration_name) DO NOTHING",
                        ("001_initial.sql",),
                    )

                cur.execute("SELECT migration_name FROM cognix_schema_migrations")
                applied = {row["migration_name"] for row in cur.fetchall()}
                for migration_name in migration_names[1:]:
                    if migration_name in applied:
                        continue
                    migration = migrations_dir / migration_name
                    cur.execute(migration.read_text())
                    cur.execute(
                        "INSERT INTO cognix_schema_migrations(migration_name) VALUES(%s) "
                        "ON CONFLICT (migration_name) DO NOTHING",
                        (migration_name,),
                    )
            conn.commit()

    def load_state(self) -> dict[str, Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sources ORDER BY created_at")
                source_rows = cur.fetchall()
                sources = {row["id"]: self._source_row(row) for row in source_rows}
                source_owners = {row["id"]: row.get("owner_id") for row in source_rows}
                cur.execute("SELECT * FROM claims ORDER BY created_at")
                for row in cur.fetchall():
                    source = sources.get(row["source_id"])
                    if source is not None:
                        source["claims"].append(self._claim_row(row))
                cur.execute("SELECT * FROM processing_tasks ORDER BY created_at")
                tasks = {row["id"]: self._task_row(row) for row in cur.fetchall()}
                cur.execute("SELECT * FROM reviews ORDER BY created_at")
                reviews = {row["source_id"]: self._review_row(row) for row in cur.fetchall()}
                cur.execute("SELECT * FROM export_jobs ORDER BY created_at")
                exports = {row["id"]: self._export_row(row) for row in cur.fetchall()}
                export_keys = {row["idempotency_key"]: row["id"] for row in exports.values()}
                cur.execute("SELECT * FROM activity_events ORDER BY created_at DESC")
                activity = [self._activity_row(row) for row in cur.fetchall()]
                # Keep startup state bounded: chapters/chunks are loaded on demand by book APIs.
                cur.execute("SELECT * FROM books ORDER BY created_at")
                book_rows = cur.fetchall()
                books = {row["id"]: self._book_row(row) for row in book_rows}
                book_owners = {row["id"]: row.get("owner_id") for row in book_rows}
        return {
            "sources": sources, "tasks": tasks, "reviews": reviews, "exports": exports,
            "activity": activity, "export_keys": export_keys, "brain_books": books,
            "source_owners": source_owners, "brain_book_owners": book_owners,
            "brain_notes": {}, "brain_concepts": {}, "brain_concept_links": {},
            "brain_note_owners": {}, "brain_concept_owners": {},
        }

    def list_books(
        self,
        limit: int = 50,
        offset: int = 0,
        owner_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT count(*) AS total FROM books")
                    total = int(cur.fetchone()["total"])
                    cur.execute(
                        """SELECT b.*, count(c.id) AS chunk_count
                           FROM books b
                           LEFT JOIN chapters ch ON ch.book_id=b.id
                           LEFT JOIN chunks c ON c.chapter_id=ch.id
                           GROUP BY b.id
                           ORDER BY b.updated_at DESC
                           LIMIT %s OFFSET %s""",
                        (limit, offset),
                    )
                else:
                    cur.execute("SELECT count(*) AS total FROM books WHERE owner_id=%s", (owner_id,))
                    total = int(cur.fetchone()["total"])
                    cur.execute(
                        """SELECT b.*, count(c.id) AS chunk_count
                           FROM books b
                           LEFT JOIN chapters ch ON ch.book_id=b.id
                           LEFT JOIN chunks c ON c.chapter_id=ch.id
                           WHERE b.owner_id=%s
                           GROUP BY b.id
                           ORDER BY b.updated_at DESC
                           LIMIT %s OFFSET %s""",
                        (owner_id, limit, offset),
                    )
                items = []
                for row in cur.fetchall():
                    item = self._book_row(row)
                    item["chunk_count"] = int(row.get("chunk_count") or 0)
                    items.append(item)
        return items, total

    def get_book(self, book_id: str, owner_id: str | None = None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM books WHERE id=%s", (book_id,))
                else:
                    cur.execute("SELECT * FROM books WHERE id=%s AND owner_id=%s", (book_id, owner_id))
                row = cur.fetchone()
                if row is None:
                    return None
                book = self._book_row(row)
                cur.execute("SELECT * FROM chapters WHERE book_id=%s ORDER BY chapter_number", (book_id,))
                chapters = [self._chapter_row(item) for item in cur.fetchall()]
                chapter_index = {chapter["id"]: chapter for chapter in chapters}
                cur.execute(
                    """SELECT * FROM chunks
                       WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id=%s)
                       ORDER BY chapter_id, sequence""",
                    (book_id,),
                )
                for item in cur.fetchall():
                    chapter = chapter_index.get(item["chapter_id"])
                    if chapter is not None:
                        chapter["chunks"].append(self._chunk_row(item))
                        book["chunk_count"] += 1
                book["chapters"] = chapters
                return book

    def search_book(
        self,
        book_id: str,
        query: str,
        limit: int = 20,
        owner_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        query = query.strip()
        if not query:
            return [], 0
        limit = max(1, min(limit, 100))
        terms = [term for term in query.lower().split() if term]
        pattern = "%" + "%".join(terms) + "%"
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        """SELECT c.id AS chunk_id, c.chapter_id, ch.title AS chapter_title,
                                  c.sequence, c.content
                           FROM chunks c
                           JOIN chapters ch ON ch.id=c.chapter_id
                           WHERE ch.book_id=%s AND lower(c.content) LIKE %s
                           ORDER BY c.sequence
                           LIMIT %s""",
                        (book_id, pattern, limit),
                    )
                else:
                    cur.execute(
                        """SELECT c.id AS chunk_id, c.chapter_id, ch.title AS chapter_title,
                                  c.sequence, c.content
                           FROM chunks c
                           JOIN chapters ch ON ch.id=c.chapter_id
                           JOIN books b ON b.id=ch.book_id
                           WHERE b.id=%s AND b.owner_id=%s AND lower(c.content) LIKE %s
                           ORDER BY c.sequence
                           LIMIT %s""",
                        (book_id, owner_id, pattern, limit),
                    )
                rows = cur.fetchall()
        matches = []
        for row in rows:
            haystack = row["content"].lower()
            score = sum(haystack.count(term) for term in terms)
            matches.append({
                "chunk_id": row["chunk_id"], "chapter_id": row["chapter_id"],
                "chapter_title": row["chapter_title"], "sequence": row["sequence"],
                "score": score, "content": row["content"],
            })
        matches.sort(key=lambda item: item["score"], reverse=True)
        return matches, len(matches)

    def get_source_for_owner(self, source_id: str, owner_id: str | None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM sources WHERE id=%s", (source_id,))
                else:
                    cur.execute(
                        "SELECT * FROM sources WHERE id=%s AND owner_id=%s",
                        (source_id, owner_id),
                    )
                row = cur.fetchone()
                if row is None:
                    return None
                source = self._source_row(row)
                cur.execute("SELECT * FROM claims WHERE source_id=%s ORDER BY created_at", (source_id,))
                source["claims"] = [self._claim_row(claim) for claim in cur.fetchall()]
                return source

    def list_sources_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM sources ORDER BY created_at")
                else:
                    cur.execute(
                        "SELECT * FROM sources WHERE owner_id=%s ORDER BY created_at",
                        (owner_id,),
                    )
                sources = {row["id"]: self._source_row(row) for row in cur.fetchall()}
                if sources:
                    cur.execute(
                        "SELECT * FROM claims WHERE source_id = ANY(%s) ORDER BY created_at",
                        (list(sources),),
                    )
                    for claim in cur.fetchall():
                        sources[claim["source_id"]]["claims"].append(self._claim_row(claim))
        return list(sources.values())

    def get_task_for_owner(self, task_id: str, owner_id: str | None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM processing_tasks WHERE id=%s", (task_id,))
                else:
                    cur.execute(
                        """SELECT t.* FROM processing_tasks t
                           JOIN sources s ON s.id=t.source_id
                           WHERE t.id=%s AND s.owner_id=%s""",
                        (task_id, owner_id),
                    )
                row = cur.fetchone()
        return self._task_row(row) if row is not None else None

    def list_tasks_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM processing_tasks ORDER BY created_at")
                else:
                    cur.execute(
                        """SELECT t.* FROM processing_tasks t
                           JOIN sources s ON s.id=t.source_id
                           WHERE s.owner_id=%s
                           ORDER BY t.created_at""",
                        (owner_id,),
                    )
                return [self._task_row(row) for row in cur.fetchall()]

    def get_book_by_content_hash(
        self,
        content_hash: str,
        owner_id: str | None,
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        "SELECT * FROM books WHERE content_hash=%s ORDER BY created_at LIMIT 1",
                        (content_hash,),
                    )
                else:
                    cur.execute(
                        """SELECT * FROM books
                           WHERE content_hash=%s AND owner_id=%s
                           ORDER BY created_at LIMIT 1""",
                        (content_hash, owner_id),
                    )
                row = cur.fetchone()
        return self._book_row(row) if row is not None else None

    @staticmethod
    def _save_source_with_cursor(cur, source: dict[str, Any], owner_id: str | None) -> None:
        cur.execute(
            """INSERT INTO sources (
                id, url, status, processing_stage, source_trust, original_text, ai_summary,
                myanmar_translation, human_edited_myanmar, approved_myanmar, note,
                critical_warnings, key_points, owner_id, created_at, updated_at
            ) VALUES (
                %(id)s, %(url)s, %(status)s, %(processing_stage)s, %(source_trust)s,
                %(original_text)s, %(ai_summary)s, %(myanmar_translation)s,
                %(human_edited_myanmar)s, %(approved_myanmar)s, %(note)s,
                %(critical_warnings)s, %(key_points)s, %(owner_id)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                url=EXCLUDED.url, status=EXCLUDED.status, processing_stage=EXCLUDED.processing_stage,
                source_trust=EXCLUDED.source_trust, original_text=EXCLUDED.original_text,
                ai_summary=EXCLUDED.ai_summary, myanmar_translation=EXCLUDED.myanmar_translation,
                human_edited_myanmar=EXCLUDED.human_edited_myanmar,
                approved_myanmar=EXCLUDED.approved_myanmar, note=EXCLUDED.note,
                critical_warnings=EXCLUDED.critical_warnings, key_points=EXCLUDED.key_points,
                updated_at=EXCLUDED.updated_at
            WHERE sources.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id
            RETURNING id""",
            {
                **source,
                "owner_id": owner_id,
                "critical_warnings": Jsonb(source.get("critical_warnings", [])),
                "key_points": Jsonb(source.get("key_points", [])),
            },
        )
        if cur.fetchone() is None:
            raise RuntimeError("Source ownership mismatch during persistence")
        cur.execute("DELETE FROM claims WHERE source_id = %s", (source["id"],))
        for claim in source.get("claims", []):
            cur.execute(
                """INSERT INTO claims (
                    id, source_id, claim_text, excerpt, location, confidence, verification_state, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (claim["id"], source["id"], claim["text"], claim.get("excerpt"), claim.get("location"),
                 claim.get("confidence"), claim.get("verification_state"), claim.get("created_at")),
            )

    def save_source(self, source: dict[str, Any], owner_id: str | None = None) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                self._save_source_with_cursor(cur, source, owner_id)
            conn.commit()

    def save_processing_transition(
        self,
        task: dict[str, Any],
        source: dict[str, Any],
        source_owner_id: str | None,
        expected_status: str,
        expected_stage: str,
        claim_token: str | None = None,
    ) -> bool:
        if claim_token is None and task["status"] != "queued":
            return False
        with self.connect() as conn:
            with conn.cursor() as cur:
                if claim_token is None:
                    cur.execute(
                        """UPDATE processing_tasks
                           SET claimed_by=NULL, claimed_at=NULL,
                               stage=%s, progress=%s, status=%s, retry_count=%s,
                               error=%s, updated_at=now()
                           WHERE id=%s
                             AND status=%s AND stage=%s
                             AND (
                               (claimed_by IS NULL AND claimed_at IS NULL)
                               OR (
                                 status='failed'
                                 AND claimed_at < now() - interval '30 minutes'
                               )
                             )
                           RETURNING id""",
                        (
                            task["stage"], task["progress"], task["status"], task["retry_count"],
                            task.get("error"), task["id"],
                            expected_status, expected_stage,
                        ),
                    )
                else:
                    cur.execute(
                        """UPDATE processing_tasks
                           SET stage=%s, progress=%s, status=%s, retry_count=%s,
                               error=%s, updated_at=%s
                           WHERE id=%s AND claimed_by=%s
                             AND status=%s AND stage=%s
                             AND claimed_at >= now() - interval '30 minutes'
                           RETURNING id""",
                        (
                            task["stage"], task["progress"], task["status"], task["retry_count"],
                            task.get("error"), task["updated_at"], task["id"], claim_token,
                            expected_status, expected_stage,
                        ),
                    )
                if cur.fetchone() is None:
                    return False
                self._save_source_with_cursor(cur, source, source_owner_id)
            conn.commit()
        return True

    def save_task(self, task: dict[str, Any]) -> None:
        if task["status"] != "queued":
            raise ValueError("New processing tasks must start queued")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO processing_tasks (
                        id, source_id, stage, progress, status, retry_count, error, idempotency_key, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(source_id)s, %(stage)s, %(progress)s, %(status)s,
                        %(retry_count)s, %(error)s, %(idempotency_key)s, %(created_at)s, %(updated_at)s
                    )
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id""",
                    task,
                )
                if cur.fetchone() is None:
                    raise RuntimeError("Processing task ID already exists")
            conn.commit()

    def save_review(self, review: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO reviews (source_id, status, note, created_at)
                       VALUES (%s, %s, %s, COALESCE(%s, now()))
                       ON CONFLICT (source_id) DO UPDATE SET
                         status=EXCLUDED.status, note=EXCLUDED.note, created_at=EXCLUDED.created_at""",
                    (review["source_id"], review["status"], review.get("note"), review.get("created_at")),
                )
            conn.commit()

    def create_export_if_absent(self, job: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO export_jobs (
                        id, source_id, destination, status, idempotency_key, safe_reference, files,
                        drive_reference, error, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING *""",
                    (job["id"], job["source_id"], "google_drive", job["status"], job["idempotency_key"],
                     job.get("drive_reference"), Jsonb(job.get("files", [])), job.get("drive_reference"),
                     job.get("error"), job.get("created_at"), job.get("updated_at")),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute("SELECT * FROM export_jobs WHERE idempotency_key = %s", (job["idempotency_key"],))
                    row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("Export idempotency lookup failed")
        return self._export_row(row)

    def save_export(self, job: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO export_jobs (
                        id, source_id, destination, status, idempotency_key, safe_reference, files,
                        drive_reference, error, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status=EXCLUDED.status, safe_reference=EXCLUDED.safe_reference,
                        files=EXCLUDED.files, drive_reference=EXCLUDED.drive_reference,
                        error=EXCLUDED.error, updated_at=EXCLUDED.updated_at""",
                    (job["id"], job["source_id"], "google_drive", job["status"], job["idempotency_key"],
                     job.get("drive_reference"), Jsonb(job.get("files", [])), job.get("drive_reference"),
                     job.get("error"), job.get("created_at"), job.get("updated_at")),
                )
            conn.commit()

    def save_brain_book(self, book: dict[str, Any], owner_id: str | None = None) -> None:
        book_params = {
            **book,
            "owner_id": owner_id,
            "binary_storage": book.get("binary_storage"),
            "binary_path": book.get("binary_path"),
            "binary_sha256": book.get("binary_sha256") or book.get("content_hash"),
            "original_filename": book.get("original_filename"),
            "processing_stage": book.get("processing_stage") or "queued",
            "processing_attempts": book.get("processing_attempts") or 0,
            "processing_error": book.get("processing_error"),
            "processing_started_at": book.get("processing_started_at"),
            "processed_at": book.get("processed_at"),
        }
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books (
                        id, title, author, language, file_type, source_kind, source_url, status,
                        description, content_hash, owner_id, binary_storage, binary_path, binary_sha256,
                        original_filename, processing_stage, processing_attempts, processing_error,
                        processing_started_at, processed_at, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(title)s, %(author)s, %(language)s, %(file_type)s, %(source_kind)s,
                        %(source_url)s, %(status)s, %(description)s, %(content_hash)s, %(owner_id)s,
                        %(binary_storage)s, %(binary_path)s, %(binary_sha256)s,
                        %(original_filename)s, %(processing_stage)s, %(processing_attempts)s, %(processing_error)s,
                        %(processing_started_at)s, %(processed_at)s, %(created_at)s, %(updated_at)s)
                    ON CONFLICT (id) DO UPDATE SET
                        title=EXCLUDED.title, author=EXCLUDED.author, language=EXCLUDED.language,
                        file_type=EXCLUDED.file_type, source_url=EXCLUDED.source_url, status=EXCLUDED.status,
                        description=EXCLUDED.description, content_hash=EXCLUDED.content_hash,
                        binary_storage=EXCLUDED.binary_storage, binary_path=EXCLUDED.binary_path,
                        binary_sha256=EXCLUDED.binary_sha256, original_filename=EXCLUDED.original_filename,
                        processing_stage=EXCLUDED.processing_stage, processing_attempts=EXCLUDED.processing_attempts,
                        processing_error=EXCLUDED.processing_error, processing_started_at=EXCLUDED.processing_started_at,
                        processed_at=EXCLUDED.processed_at, updated_at=EXCLUDED.updated_at
                    WHERE books.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id
                    RETURNING id""",
                    book_params,
                )
                if cur.fetchone() is None:
                    raise RuntimeError("Book ownership mismatch during persistence")
                cur.execute("DELETE FROM chunks WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id = %s)", (book["id"],))
                cur.execute("DELETE FROM chapters WHERE book_id = %s", (book["id"],))
                for chapter in book.get("chapters", []):
                    cur.execute(
                        "INSERT INTO chapters (id, book_id, chapter_number, title, created_at) VALUES (%s, %s, %s, %s, %s)",
                        (chapter["id"], book["id"], chapter["chapter_number"], chapter["title"], chapter["created_at"]),
                    )
                    for chunk in chapter.get("chunks", []):
                        cur.execute(
                            """INSERT INTO chunks (
                                id, chapter_id, sequence, content, page_number, start_offset, end_offset, token_count, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (chunk["id"], chapter["id"], chunk["sequence"], chunk["content"], chunk.get("page_number"),
                             chunk.get("start_offset"), chunk.get("end_offset"), chunk.get("token_count"), chunk["created_at"]),
                        )
            conn.commit()

    def list_brain_notes_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM notes ORDER BY updated_at DESC")
                else:
                    cur.execute("SELECT * FROM notes WHERE owner_id=%s ORDER BY updated_at DESC", (owner_id,))
                rows = cur.fetchall()
                notes = {row["id"]: self._note_row(row) for row in rows}
                if notes:
                    cur.execute("SELECT * FROM note_sources WHERE note_id = ANY(%s) ORDER BY created_at", (list(notes),))
                    for row in cur.fetchall():
                        notes[row["note_id"]]["sources"].append(
                            {"source_type": row["source_type"], "source_id": row["source_id"]}
                        )
        return list(notes.values())

    def get_brain_note_for_owner(self, note_id: str, owner_id: str | None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM notes WHERE id=%s", (note_id,))
                else:
                    cur.execute("SELECT * FROM notes WHERE id=%s AND owner_id=%s", (note_id, owner_id))
                row = cur.fetchone()
                if row is None:
                    return None
                note = self._note_row(row)
                cur.execute("SELECT * FROM note_sources WHERE note_id=%s ORDER BY created_at", (note_id,))
                note["sources"] = [
                    {"source_type": source["source_type"], "source_id": source["source_id"]}
                    for source in cur.fetchall()
                ]
                return note

    def list_note_backlinks_for_owner(self, note_id: str, owner_id: str | None) -> list[dict[str, Any]] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT id FROM notes WHERE id=%s", (note_id,))
                    target = cur.fetchone()
                    if target is None:
                        return None
                    cur.execute(
                        """SELECT DISTINCT n.* FROM notes n
                           JOIN note_sources ns ON ns.note_id=n.id
                           WHERE ns.source_type='note' AND ns.source_id=%s
                           ORDER BY n.updated_at DESC""",
                        (note_id,),
                    )
                else:
                    cur.execute("SELECT id FROM notes WHERE id=%s AND owner_id=%s", (note_id, owner_id))
                    target = cur.fetchone()
                    if target is None:
                        return None
                    cur.execute(
                        """SELECT DISTINCT n.* FROM notes n
                           JOIN note_sources ns ON ns.note_id=n.id
                           WHERE ns.source_type='note' AND ns.source_id=%s AND n.owner_id=%s
                           ORDER BY n.updated_at DESC""",
                        (note_id, owner_id),
                    )
                notes = {row["id"]: self._note_row(row) for row in cur.fetchall()}
                if notes:
                    cur.execute(
                        "SELECT * FROM note_sources WHERE note_id = ANY(%s) ORDER BY created_at",
                        (list(notes),),
                    )
                    for row in cur.fetchall():
                        notes[row["note_id"]]["sources"].append(
                            {"source_type": row["source_type"], "source_id": row["source_id"]}
                        )
                return list(notes.values())

    def save_brain_note(self, note: dict[str, Any], owner_id: str | None) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO notes (id, title, content, note_type, status, owner_id, created_at, updated_at)
                       VALUES (%(id)s, %(title)s, %(content)s, %(note_type)s, %(status)s, %(owner_id)s, %(created_at)s, %(updated_at)s)
                       ON CONFLICT (id) DO UPDATE SET
                         title=EXCLUDED.title, content=EXCLUDED.content, note_type=EXCLUDED.note_type,
                         status=EXCLUDED.status, updated_at=EXCLUDED.updated_at
                       WHERE notes.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id
                       RETURNING id""",
                    {**note, "owner_id": owner_id},
                )
                if cur.fetchone() is None:
                    raise RuntimeError("Note ownership mismatch during persistence")
                cur.execute("DELETE FROM note_sources WHERE note_id=%s", (note["id"],))
                if note.get("source_type") and note.get("source_id"):
                    if owner_id is None:
                        cur.execute(
                            """INSERT INTO note_sources(note_id,source_type,source_id)
                               VALUES(%s,%s,%s) ON CONFLICT DO NOTHING""",
                            (note["id"], note["source_type"], note["source_id"]),
                        )
                    else:
                        parent_tables = {
                            "note": "notes",
                            "source": "sources",
                            "book": "books",
                            "concept": "concepts",
                        }
                        parent_table = parent_tables.get(note["source_type"])
                        if parent_table is None:
                            raise RuntimeError("Unsupported note reference type")
                        cur.execute(
                            f"""INSERT INTO note_sources(note_id,source_type,source_id)
                                SELECT %s,%s,parent.id FROM {parent_table} parent
                                WHERE parent.id=%s AND parent.owner_id=%s
                                ON CONFLICT DO NOTHING""",
                            (note["id"], note["source_type"], note["source_id"], owner_id),
                        )
                        if cur.rowcount == 0:
                            raise RuntimeError("Note reference ownership mismatch")
            conn.commit()

    def list_brain_concepts_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM concepts ORDER BY name")
                else:
                    cur.execute("SELECT * FROM concepts WHERE owner_id=%s ORDER BY name", (owner_id,))
                return [self._concept_row(row) for row in cur.fetchall()]

    def get_brain_concept_for_owner(self, concept_id: str, owner_id: str | None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM concepts WHERE id=%s", (concept_id,))
                else:
                    cur.execute("SELECT * FROM concepts WHERE id=%s AND owner_id=%s", (concept_id, owner_id))
                row = cur.fetchone()
        return self._concept_row(row) if row is not None else None

    def get_brain_concept_by_name_for_owner(
        self,
        name: str,
        owner_id: str | None,
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        "SELECT * FROM concepts WHERE lower(name)=lower(%s) ORDER BY created_at LIMIT 1",
                        (name,),
                    )
                else:
                    cur.execute(
                        """SELECT * FROM concepts
                           WHERE owner_id=%s AND lower(name)=lower(%s)
                           ORDER BY created_at LIMIT 1""",
                        (owner_id, name),
                    )
                row = cur.fetchone()
        return self._concept_row(row) if row is not None else None

    def list_concept_links_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute("SELECT * FROM concept_links ORDER BY created_at")
                else:
                    cur.execute(
                        """SELECT l.* FROM concept_links l
                           JOIN concepts source ON source.id=l.from_concept_id
                           JOIN concepts target ON target.id=l.to_concept_id
                           WHERE source.owner_id=%s AND target.owner_id=%s
                           ORDER BY l.created_at""",
                        (owner_id, owner_id),
                    )
                return [self._concept_link_row(row) for row in cur.fetchall()]

    def save_brain_concept(self, concept: dict[str, Any], owner_id: str | None) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO concepts (id, name, description, owner_id, created_at, updated_at)
                       VALUES (%(id)s, %(name)s, %(description)s, %(owner_id)s, %(created_at)s, %(updated_at)s)
                       ON CONFLICT (id) DO UPDATE SET
                         name=EXCLUDED.name, description=EXCLUDED.description, updated_at=EXCLUDED.updated_at
                       WHERE concepts.owner_id IS NOT DISTINCT FROM EXCLUDED.owner_id
                       RETURNING id""",
                    {**concept, "owner_id": owner_id},
                )
                if cur.fetchone() is None:
                    raise RuntimeError("Concept ownership mismatch during persistence")
            conn.commit()

    @staticmethod
    def _book_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "title": row["title"], "author": row.get("author"), "language": row["language"],
                "file_type": row["file_type"], "source_kind": row["source_kind"], "source_url": row.get("source_url"),
                "status": row["status"], "description": row.get("description"), "content_hash": row.get("content_hash"),
                "binary_storage": row.get("binary_storage"), "binary_path": row.get("binary_path"),
                "binary_sha256": row.get("binary_sha256"), "original_filename": row.get("original_filename"),
                "processing_stage": row.get("processing_stage") or "queued",
                "processing_attempts": row.get("processing_attempts") or 0,
                "processing_error": row.get("processing_error"),
                "processing_started_at": row.get("processing_started_at").isoformat() if row.get("processing_started_at") else None,
                "processed_at": row.get("processed_at").isoformat() if row.get("processed_at") else None,
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(), "chapters": [], "chunk_count": 0}

    @staticmethod
    def _chapter_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "book_id": row["book_id"], "chapter_number": row["chapter_number"],
                "title": row["title"], "created_at": row["created_at"].isoformat(), "chunks": []}

    @staticmethod
    def _chunk_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "chapter_id": row["chapter_id"], "sequence": row["sequence"], "content": row["content"],
                "page_number": row.get("page_number"), "start_offset": row.get("start_offset"),
                "end_offset": row.get("end_offset"), "token_count": row.get("token_count"),
                "created_at": row["created_at"].isoformat()}

    @staticmethod
    def _note_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "title": row["title"], "content": row["content"], "note_type": row["note_type"],
                "status": row["status"], "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat(),
                "sources": []}

    @staticmethod
    def _concept_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "name": row["name"], "description": row.get("description"),
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}

    @staticmethod
    def _concept_link_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "from_concept_id": row["from_concept_id"], "to_concept_id": row["to_concept_id"],
                "relation": row["relation"], "weight": float(row["weight"]), "created_at": row["created_at"].isoformat()}

    def save_brain_concept_link(self, link: dict[str, Any], owner_id: str | None) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        """INSERT INTO concept_links (id, from_concept_id, to_concept_id, relation, weight, created_at)
                           VALUES (%(id)s, %(from_concept_id)s, %(to_concept_id)s, %(relation)s, %(weight)s, %(created_at)s)
                           ON CONFLICT (from_concept_id, to_concept_id, relation) DO UPDATE SET weight=EXCLUDED.weight
                           RETURNING id""",
                        link,
                    )
                else:
                    cur.execute(
                        """INSERT INTO concept_links (id, from_concept_id, to_concept_id, relation, weight, created_at)
                           SELECT %(id)s, source.id, target.id, %(relation)s, %(weight)s, %(created_at)s
                           FROM concepts source JOIN concepts target ON target.id=%(to_concept_id)s
                           WHERE source.id=%(from_concept_id)s
                             AND source.owner_id=%(owner_id)s AND target.owner_id=%(owner_id)s
                           ON CONFLICT (from_concept_id, to_concept_id, relation)
                           DO UPDATE SET weight=EXCLUDED.weight
                           RETURNING id""",
                        {**link, "owner_id": owner_id},
                    )
                if cur.fetchone() is None:
                    raise RuntimeError("Concept link ownership mismatch during persistence")
            conn.commit()

    def create_language_card(self, card: dict[str, Any], owner_id: str | None) -> dict[str, Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO language_cards(id,front,back,language,source_note,owner_id)
                       VALUES(%(id)s,%(front)s,%(back)s,%(language)s,%(source_note)s,%(owner_id)s)
                       RETURNING id,front,back,language,source_note,due_at,stability,difficulty,
                                 reps,lapses,state,created_at,updated_at""",
                    {**card, "owner_id": owner_id},
                )
                row = cur.fetchone()
            conn.commit()
        return row

    def save_vault_item(self, item: dict[str, Any], owner_id: str | None) -> dict[str, Any]:
        """Persist a vault item with optional owner scoping."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO vault_items(id,label,ciphertext,nonce,kdf_salt,kdf_params,owner_id)
                       VALUES(%(id)s,%(label)s,%(ciphertext)s,%(nonce)s,%(kdf_salt)s,%(kdf_params)s,%(owner_id)s)
                       RETURNING id,label,nonce,kdf_salt,kdf_params,created_at,updated_at""",
                    {**item, "owner_id": owner_id},
                )
                row = cur.fetchone()
            conn.commit()
        return row

    def get_vault_item_for_owner(self, item_id: str, owner_id: str | None) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        "SELECT id,label,ciphertext,nonce,kdf_salt,kdf_params,created_at,updated_at FROM vault_items WHERE id=%s",
                        (item_id,),
                    )
                else:
                    cur.execute(
                        "SELECT id,label,ciphertext,nonce,kdf_salt,kdf_params,created_at,updated_at FROM vault_items WHERE id=%s AND owner_id=%s",
                        (item_id, owner_id),
                    )
                return cur.fetchone()

    def list_vault_items_for_owner(self, owner_id: str | None) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        "SELECT id,label,nonce,kdf_salt,kdf_params,created_at,updated_at FROM vault_items ORDER BY updated_at DESC",
                    )
                else:
                    cur.execute(
                        "SELECT id,label,nonce,kdf_salt,kdf_params,created_at,updated_at FROM vault_items WHERE owner_id=%s ORDER BY updated_at DESC",
                        (owner_id,),
                    )
                return cur.fetchall()

        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO language_cards(id,front,back,language,source_note,owner_id)
                       VALUES(%(id)s,%(front)s,%(back)s,%(language)s,%(source_note)s,%(owner_id)s)
                       RETURNING id,front,back,language,source_note,due_at,stability,difficulty,
                                 reps,lapses,state,created_at,updated_at""",
                    {**card, "owner_id": owner_id},
                )
                row = cur.fetchone()
            conn.commit()
        return row

    def list_language_cards_due_for_owner(self, owner_id: str | None, limit: int) -> list[dict[str, Any]]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        """SELECT id,front,back,language,source_note,due_at,stability,difficulty,
                                  reps,lapses,state,created_at,updated_at
                           FROM language_cards WHERE due_at<=now() ORDER BY due_at LIMIT %s""",
                        (limit,),
                    )
                else:
                    cur.execute(
                        """SELECT id,front,back,language,source_note,due_at,stability,difficulty,
                                  reps,lapses,state,created_at,updated_at
                           FROM language_cards
                           WHERE owner_id=%s AND due_at<=now() ORDER BY due_at LIMIT %s""",
                        (owner_id, limit),
                    )
                return cur.fetchall()

    def review_language_card(
        self,
        card_id: str,
        owner_id: str | None,
        rating: int,
        schedule: Callable[[dict[str, Any], int], tuple[float, float, int, int, str, Any]],
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                if owner_id is None:
                    cur.execute(
                        """SELECT id,front,back,language,source_note,due_at,stability,difficulty,
                                  reps,lapses,state,created_at,updated_at
                           FROM language_cards WHERE id=%s FOR UPDATE""",
                        (card_id,),
                    )
                else:
                    cur.execute(
                        """SELECT id,front,back,language,source_note,due_at,stability,difficulty,
                                  reps,lapses,state,created_at,updated_at
                           FROM language_cards WHERE id=%s AND owner_id=%s FOR UPDATE""",
                        (card_id, owner_id),
                    )
                card = cur.fetchone()
                if card is None:
                    return None
                stability, difficulty, reps, lapses, state, due = schedule(card, rating)
                if owner_id is None:
                    cur.execute(
                        """UPDATE language_cards SET stability=%s,difficulty=%s,reps=%s,lapses=%s,
                                  state=%s,due_at=%s,updated_at=now()
                           WHERE id=%s
                           RETURNING id,front,back,language,source_note,due_at,stability,difficulty,
                                     reps,lapses,state,created_at,updated_at""",
                        (stability, difficulty, reps, lapses, state, due, card_id),
                    )
                else:
                    cur.execute(
                        """UPDATE language_cards SET stability=%s,difficulty=%s,reps=%s,lapses=%s,
                                  state=%s,due_at=%s,updated_at=now()
                           WHERE id=%s AND owner_id=%s
                           RETURNING id,front,back,language,source_note,due_at,stability,difficulty,
                                     reps,lapses,state,created_at,updated_at""",
                        (stability, difficulty, reps, lapses, state, due, card_id, owner_id),
                    )
                updated = cur.fetchone()
                if updated is None:
                    return None
                cur.execute(
                    "INSERT INTO language_reviews(id,card_id,rating,scheduled_for) VALUES(%s,%s,%s,%s)",
                    (f"REV-{uuid4().hex[:8].upper()}", card_id, rating, due),
                )
            conn.commit()
        return updated

    def add_activity(self, event: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO activity_events (id, action, target, previous_state, new_state, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING""",
                    (event["id"], event["action"], event["target"], event["previous_state"], event["new_state"], event["timestamp"]),
                )
            conn.commit()

    @staticmethod
    def _source_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "url": row["url"], "note": row.get("note"), "status": row["status"],
                "processing_stage": row["processing_stage"], "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(), "original_text": row.get("original_text"),
                "ai_summary": row.get("ai_summary"), "myanmar_translation": row.get("myanmar_translation"),
                "human_edited_myanmar": row.get("human_edited_myanmar"), "approved_myanmar": row.get("approved_myanmar"),
                "source_trust": row.get("source_trust") or "unverified", "claims": [],
                "critical_warnings": row.get("critical_warnings") or [], "key_points": row.get("key_points") or []}

    @staticmethod
    def _claim_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "text": row["claim_text"], "excerpt": row.get("excerpt"), "location": row.get("location"),
                "confidence": str(row.get("confidence") or "medium"), "verification_state": row["verification_state"],
                "created_at": row["created_at"].isoformat()}

    @staticmethod
    def _task_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "source_id": row["source_id"], "stage": row["stage"], "progress": row["progress"],
                "status": row["status"], "retry_count": row["retry_count"], "error": row.get("error"),
                "idempotency_key": row.get("idempotency_key"), "superseded_by": row.get("superseded_by"),
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}

    @staticmethod
    def _review_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"source_id": row["source_id"], "status": row["status"], "note": row.get("note"),
                "created_at": row["created_at"].isoformat()}

    @staticmethod
    def _export_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "source_id": row["source_id"], "status": row["status"],
                "idempotency_key": row["idempotency_key"], "drive_reference": row.get("drive_reference") or row.get("safe_reference"),
                "error": row.get("error"), "files": row.get("files") or [],
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}

    @staticmethod
    def _activity_row(row: dict[str, Any]) -> dict[str, Any]:
        return {"id": row["id"], "action": row["action"], "target": row["target"],
                "previous_state": row.get("previous_state") or "—", "new_state": row.get("new_state") or "—",
                "timestamp": row["created_at"].isoformat()}


def configured_database() -> Database | None:
    dsn = os.getenv("DATABASE_URL")
    return Database(dsn) if dsn else None
