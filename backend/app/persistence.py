from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class Database:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

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
                migration_003 = migrations_dir / "003_persistence_hardening.sql"
                if migration_003.exists():
                    cur.execute(migration_003.read_text())
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

        return {
            "sources": sources,
            "tasks": tasks,
            "reviews": reviews,
            "exports": exports,
            "activity": activity,
            "export_keys": export_keys,
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
                        safe_reference, files, drive_reference, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING *
                    """,
                    (
                        job["id"], job["source_id"], "google_drive", job["status"],
                        job["idempotency_key"], job.get("drive_reference"),
                        Jsonb(job.get("files", [])), job.get("drive_reference"),
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
                        safe_reference, files, drive_reference, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        COALESCE(%s, now()), COALESCE(%s, now())
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status=EXCLUDED.status,
                        safe_reference=EXCLUDED.safe_reference,
                        files=EXCLUDED.files,
                        drive_reference=EXCLUDED.drive_reference,
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
                        job.get("created_at"),
                        job.get("updated_at"),
                    ),
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
