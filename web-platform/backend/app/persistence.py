from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._task_lock_connections: dict[str, Any] = {}

    def try_claim_task(self, task_id: str) -> bool:
        """Claim a task with a PostgreSQL advisory lock across worker processes."""
        if task_id in self._task_lock_connections:
            return True
        conn = psycopg.connect(self.dsn)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_try_advisory_lock(hashtext(%s)) AS locked", (task_id,))
                locked = bool(cur.fetchone()["locked"])
            if locked:
                self._task_lock_connections[task_id] = conn
                return True
        except Exception:
            conn.close()
            raise
        conn.close()
        return False

    def release_task(self, task_id: str) -> None:
        conn = self._task_lock_connections.pop(task_id, None)
        if conn is None:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(hashtext(%s))", (task_id,))
            conn.commit()
        finally:
            conn.close()

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

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
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT to_regclass('public.sources') AS table_name"
                )
                exists = cur.fetchone()["table_name"] is not None
                if not exists:
                    cur.execute((migrations_dir / "001_initial.sql").read_text())
                cur.execute((migrations_dir / "002_api_contract_alignment.sql").read_text())
                for migration_name in (
                    "003_persistence_hardening.sql",
                    "004_brain_vault_foundation.sql",
                    "005_brain_vault_search.sql",
                    "006_brain_vault_advanced.sql",
                    "007_book_storage.sql",
                    "008_document_and_synthesis_hardening.sql",
                    "009_media_assets.sql",
                    "010_agent_active_layer.sql",
                ):
                    migration = migrations_dir / migration_name
                    if migration.exists():
                        cur.execute(migration.read_text())
            conn.commit()

    def load_state(self) -> dict[str, Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM sources ORDER BY created_at")
                sources = {row["id"]: self._source_row(row) for row in cur.fetchall()}

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
                export_keys = {
                    row["idempotency_key"]: row["id"] for row in exports.values()
                }

                cur.execute("SELECT * FROM activity_events ORDER BY created_at DESC")
                activity = [self._activity_row(row) for row in cur.fetchall()]

                cur.execute("SELECT * FROM books ORDER BY created_at")
                books = {row["id"]: self._book_row(row) for row in cur.fetchall()}
                cur.execute("SELECT * FROM chapters ORDER BY book_id, chapter_number")
                for row in cur.fetchall():
                    book = books.get(row["book_id"])
                    if book is not None:
                        book["chapters"].append(self._chapter_row(row))
                cur.execute("SELECT * FROM chunks ORDER BY chapter_id, sequence")
                chapter_index = {
                    chapter["id"]: (book, chapter)
                    for book in books.values()
                    for chapter in book["chapters"]
                }
                for row in cur.fetchall():
                    target = chapter_index.get(row["chapter_id"])
                    if target is not None:
                        book, chapter = target
                        chapter["chunks"].append(self._chunk_row(row))
                        book["chunk_count"] += 1

                cur.execute("SELECT * FROM notes ORDER BY updated_at DESC")
                notes = {row["id"]: self._note_row(row) for row in cur.fetchall()}
                cur.execute("SELECT * FROM note_sources ORDER BY created_at")
                for row in cur.fetchall():
                    note = notes.get(row["note_id"])
                    if note is not None:
                        note["sources"].append({
                            "source_type": row["source_type"],
                            "source_id": row["source_id"],
                        })

                cur.execute("SELECT * FROM concepts ORDER BY name")
                concepts = {row["id"]: self._concept_row(row) for row in cur.fetchall()}
                cur.execute("SELECT * FROM concept_links ORDER BY created_at")
                concept_links = {row["id"]: self._concept_link_row(row) for row in cur.fetchall()}

        return {
            "sources": sources,
            "tasks": tasks,
            "reviews": reviews,
            "exports": exports,
            "activity": activity,
            "export_keys": export_keys,
            "brain_books": books,
            "brain_notes": notes,
            "brain_concepts": concepts,
            "brain_concept_links": concept_links,
        }

    def save_source(self, source: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sources (
                        id, url, status, processing_stage, source_trust,
                        original_text, ai_summary, myanmar_translation,
                        human_edited_myanmar, approved_myanmar, note,
                        critical_warnings, key_points, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(url)s, %(status)s, %(processing_stage)s,
                        %(source_trust)s, %(original_text)s, %(ai_summary)s,
                        %(myanmar_translation)s, %(human_edited_myanmar)s,
                        %(approved_myanmar)s, %(note)s, %(critical_warnings)s,
                        %(key_points)s, %(created_at)s, %(updated_at)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        url=EXCLUDED.url,
                        status=EXCLUDED.status,
                        processing_stage=EXCLUDED.processing_stage,
                        source_trust=EXCLUDED.source_trust,
                        original_text=EXCLUDED.original_text,
                        ai_summary=EXCLUDED.ai_summary,
                        myanmar_translation=EXCLUDED.myanmar_translation,
                        human_edited_myanmar=EXCLUDED.human_edited_myanmar,
                        approved_myanmar=EXCLUDED.approved_myanmar,
                        note=EXCLUDED.note,
                        critical_warnings=EXCLUDED.critical_warnings,
                        key_points=EXCLUDED.key_points,
                        updated_at=EXCLUDED.updated_at
                    """,
                    {**source, "critical_warnings": Jsonb(source.get("critical_warnings", [])), "key_points": Jsonb(source.get("key_points", []))},
                )
                cur.execute("DELETE FROM claims WHERE source_id = %s", (source["id"],))
                for claim in source.get("claims", []):
                    cur.execute(
                        """
                        INSERT INTO claims (
                            id, source_id, claim_text, excerpt, location,
                            confidence, verification_state, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            claim["id"],
                            source["id"],
                            claim["text"],
                            claim.get("excerpt"),
                            claim.get("location"),
                            claim.get("confidence"),
                            claim.get("verification_state"),
                            claim.get("created_at"),
                        ),
                    )
            conn.commit()

    def save_task(self, task: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO processing_tasks (
                        id, source_id, stage, progress, status,
                        retry_count, error, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(source_id)s, %(stage)s, %(progress)s, %(status)s,
                        %(retry_count)s, %(error)s, %(created_at)s, %(updated_at)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        stage=EXCLUDED.stage,
                        progress=EXCLUDED.progress,
                        status=EXCLUDED.status,
                        retry_count=EXCLUDED.retry_count,
                        error=EXCLUDED.error,
                        updated_at=EXCLUDED.updated_at
                    """,
                    task,
                )
            conn.commit()

    def save_review(self, review: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO reviews (
                        source_id, status, note, created_at
                    ) VALUES (%s, %s, %s, COALESCE(%s, now()))
                    ON CONFLICT (source_id) DO UPDATE SET
                        status=EXCLUDED.status,
                        note=EXCLUDED.note,
                        created_at=EXCLUDED.created_at
                    """,
                    (
                        review["source_id"],
                        review["status"],
                        review.get("note"),
                        review.get("created_at"),
                    ),
                )
            conn.commit()

    def create_export_if_absent(self, job: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO export_jobs (
                        id, source_id, destination, status, idempotency_key,
                        safe_reference, files, drive_reference, error, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING *
                    """,
                    (
                        job["id"], job["source_id"], "google_drive", job["status"],
                        job["idempotency_key"], job.get("drive_reference"),
                        Jsonb(job.get("files", [])), job.get("drive_reference"),
                        job.get("error"),
                        job.get("created_at"), job.get("updated_at"),
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "SELECT * FROM export_jobs WHERE idempotency_key = %s",
                        (job["idempotency_key"],),
                    )
                    row = cur.fetchone()
            conn.commit()
        if row is None:
            raise RuntimeError("Export idempotency lookup failed")
        return self._export_row(row)

    def save_export(self, job: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO export_jobs (
                        id, source_id, destination, status, idempotency_key,
                        safe_reference, files, drive_reference, error, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status=EXCLUDED.status,
                        safe_reference=EXCLUDED.safe_reference,
                        files=EXCLUDED.files,
                        drive_reference=EXCLUDED.drive_reference,
                        error=EXCLUDED.error,
                        updated_at=EXCLUDED.updated_at
                    """,
                    (
                        job["id"],
                        job["source_id"],
                        "google_drive",
                        job["status"],
                        job["idempotency_key"],
                        job.get("drive_reference"),
                        Jsonb(job.get("files", [])),
                        job.get("drive_reference"),
                        job.get("error"),
                        job.get("created_at"),
                        job.get("updated_at"),
                    ),
                )
            conn.commit()

    def save_brain_book(self, book: dict[str, Any]) -> None:
        book_params = {**book, "binary_storage": book.get("binary_storage"), "binary_path": book.get("binary_path")}
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books (
                        id, title, author, language, file_type, source_kind,
                        source_url, status, description, content_hash, binary_storage, binary_path, created_at, updated_at
                    ) VALUES (%(id)s, %(title)s, %(author)s, %(language)s, %(file_type)s,
                              %(source_kind)s, %(source_url)s, %(status)s, %(description)s,
                              %(content_hash)s, %(binary_storage)s, %(binary_path)s, %(created_at)s, %(updated_at)s)
                    ON CONFLICT (id) DO UPDATE SET
                        title=EXCLUDED.title, author=EXCLUDED.author, language=EXCLUDED.language,
                        file_type=EXCLUDED.file_type, source_url=EXCLUDED.source_url,
                        status=EXCLUDED.status, description=EXCLUDED.description,
                        content_hash=EXCLUDED.content_hash, binary_storage=EXCLUDED.binary_storage, binary_path=EXCLUDED.binary_path, updated_at=EXCLUDED.updated_at""",
                    book_params,
                )
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
                                id, chapter_id, sequence, content, page_number,
                                start_offset, end_offset, token_count, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (
                                chunk["id"], chapter["id"], chunk["sequence"], chunk["content"],
                                chunk.get("page_number"), chunk.get("start_offset"),
                                chunk.get("end_offset"), chunk.get("token_count"),
                                chunk["created_at"],
                            ),
                        )
            conn.commit()

    def save_brain_note(self, note: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO notes (id, title, content, note_type, status, created_at, updated_at)
                       VALUES (%(id)s, %(title)s, %(content)s, %(note_type)s, %(status)s, %(created_at)s, %(updated_at)s)
                       ON CONFLICT (id) DO UPDATE SET
                         title=EXCLUDED.title, content=EXCLUDED.content, note_type=EXCLUDED.note_type,
                         status=EXCLUDED.status, updated_at=EXCLUDED.updated_at""",
                    note,
                )
                cur.execute("DELETE FROM note_sources WHERE note_id = %s", (note["id"],))
                if note.get("source_type") and note.get("source_id"):
                    cur.execute(
                        "INSERT INTO note_sources (note_id, source_type, source_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                        (note["id"], note["source_type"], note["source_id"]),
                    )
            conn.commit()

    def save_brain_concept(self, concept: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO concepts (id, name, description, created_at, updated_at)
                       VALUES (%(id)s, %(name)s, %(description)s, %(created_at)s, %(updated_at)s)
                       ON CONFLICT (id) DO UPDATE SET
                         name=EXCLUDED.name, description=EXCLUDED.description, updated_at=EXCLUDED.updated_at""",
                    concept,
                )
            conn.commit()

    @staticmethod
    def _book_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "title": row["title"], "author": row.get("author"),
            "language": row["language"], "file_type": row["file_type"],
            "source_kind": row["source_kind"], "source_url": row.get("source_url"),
            "status": row["status"], "description": row.get("description"),
            "content_hash": row.get("content_hash"),
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
            "chapters": [], "chunk_count": 0,
        }

    @staticmethod
    def _chapter_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "book_id": row["book_id"],
            "chapter_number": row["chapter_number"], "title": row["title"],
            "created_at": row["created_at"].isoformat(), "chunks": [],
        }

    @staticmethod
    def _chunk_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "chapter_id": row["chapter_id"],
            "sequence": row["sequence"], "content": row["content"],
            "page_number": row.get("page_number"), "start_offset": row.get("start_offset"),
            "end_offset": row.get("end_offset"), "token_count": row.get("token_count"),
            "created_at": row["created_at"].isoformat(),
        }

    @staticmethod
    def _note_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "title": row["title"], "content": row["content"],
            "note_type": row["note_type"], "status": row["status"],
            "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat(),
            "sources": [],
        }

    @staticmethod
    def _concept_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "name": row["name"], "description": row.get("description"),
            "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat(),
        }

    @staticmethod
    def _concept_link_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"], "from_concept_id": row["from_concept_id"],
            "to_concept_id": row["to_concept_id"], "relation": row["relation"],
            "weight": float(row["weight"]), "created_at": row["created_at"].isoformat(),
        }

    def save_brain_concept_link(self, link: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO concept_links (
                        id, from_concept_id, to_concept_id, relation, weight, created_at
                    ) VALUES (%(id)s, %(from_concept_id)s, %(to_concept_id)s,
                              %(relation)s, %(weight)s, %(created_at)s)
                    ON CONFLICT (from_concept_id, to_concept_id, relation) DO UPDATE SET
                        weight=EXCLUDED.weight""",
                    link,
                )
            conn.commit()

    def add_activity(self, event: dict[str, Any]) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO activity_events (
                        id, action, target, previous_state, new_state, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        event["id"],
                        event["action"],
                        event["target"],
                        event["previous_state"],
                        event["new_state"],
                        event["timestamp"],
                    ),
                )
            conn.commit()

    @staticmethod
    def _source_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "url": row["url"],
            "note": row.get("note"),
            "status": row["status"],
            "processing_stage": row["processing_stage"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
            "original_text": row.get("original_text"),
            "ai_summary": row.get("ai_summary"),
            "myanmar_translation": row.get("myanmar_translation"),
            "human_edited_myanmar": row.get("human_edited_myanmar"),
            "approved_myanmar": row.get("approved_myanmar"),
            "source_trust": row.get("source_trust") or "unverified",
            "claims": [],
            "critical_warnings": row.get("critical_warnings") or [],
            "key_points": row.get("key_points") or [],
        }

    @staticmethod
    def _claim_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "text": row["claim_text"],
            "excerpt": row.get("excerpt"),
            "location": row.get("location"),
            "confidence": str(row.get("confidence") or "medium"),
            "verification_state": row["verification_state"],
            "created_at": row["created_at"].isoformat(),
        }

    @staticmethod
    def _task_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "source_id": row["source_id"],
            "stage": row["stage"],
            "progress": row["progress"],
            "status": row["status"],
            "retry_count": row["retry_count"],
            "error": row.get("error"),
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    @staticmethod
    def _review_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_id": row["source_id"],
            "status": row["status"],
            "note": row.get("note"),
            "created_at": row["created_at"].isoformat(),
        }

    @staticmethod
    def _export_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "source_id": row["source_id"],
            "status": row["status"],
            "idempotency_key": row["idempotency_key"],
            "drive_reference": row.get("drive_reference") or row.get("safe_reference"),
            "error": row.get("error"),
            "files": row.get("files") or [],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    @staticmethod
    def _activity_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "action": row["action"],
            "target": row["target"],
            "previous_state": row.get("previous_state") or "—",
            "new_state": row.get("new_state") or "—",
            "timestamp": row["created_at"].isoformat(),
        }


def configured_database() -> Database | None:
    dsn = os.getenv("DATABASE_URL")
    return Database(dsn) if dsn else None
