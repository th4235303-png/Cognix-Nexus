from __future__ import annotations

import asyncio
import logging
import os
import time
import threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app.services.embeddings import embedding_provider
from app.services.agent import enqueue_due_agent_schedules, run_due_agent_jobs
from app.services.export_worker import advance_export_job
from app.services.book_processing import process_queued_books, finalize_indexed_books

from app.services.processing import STAGES, TaskLeaseLost, advance
from app.services.task_retry import task_is_runnable
from app.store import store


logger = logging.getLogger("cognix.worker")

POLL_SECONDS = float(os.getenv("COGNIX_WORKER_POLL_SECONDS", "2"))
LEASE_HEARTBEAT_SECONDS = 5 * 60


def _advance_with_lease(task_id: str, claim_token: str) -> dict:
    database = store.database
    if database is None:
        raise RuntimeError("A database connection is required for a claimed task")
    lost = threading.Event()
    stop = threading.Event()

    def renew_lease() -> None:
        while not stop.wait(LEASE_HEARTBEAT_SECONDS):
            try:
                if not database.renew_task_claim(task_id, claim_token):
                    lost.set()
                    logger.warning("task_lease_renewal_lost task_id=%s", task_id)
                    return
            except Exception as exc:
                lost.set()
                logger.exception(
                    "task_lease_renewal_failed task_id=%s error_type=%s",
                    task_id,
                    type(exc).__name__,
                )
                return

    heartbeat = threading.Thread(target=renew_lease, daemon=True)
    heartbeat.start()
    try:
        return advance(
            task_id,
            claim_token=claim_token,
            lease_is_valid=lambda: not lost.is_set(),
        )
    finally:
        stop.set()
        heartbeat.join()


def _advance_exports(limit: int = 5) -> int:
    store.refresh()
    processed = 0
    for job in list(store.exports.values()):
        if processed >= limit:
            break
        if job["status"] not in {"queued", "uploading"}:
            continue
        try:
            advanced = advance_export_job(job["id"])
            if advanced.get("status") != job["status"]:
                processed += 1
        except Exception as exc:
            logger.exception(
                "export_job_processing_failed export_id=%s error_type=%s",
                job["id"],
                type(exc).__name__,
            )
            continue
    return processed

 
async def _index_unembedded_chunks(limit: int = 25) -> int:
    if not store.database or not embedding_provider.configured:
        return 0
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.content
                   FROM chunks c
                   LEFT JOIN embeddings e ON e.owner_type='chunk' AND e.owner_id=c.id
                   WHERE e.owner_id IS NULL
                   ORDER BY c.created_at
                   LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()
    if not rows:
        return 0
    vectors = await embedding_provider.embed([row["content"] for row in rows])
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            for row, vector in zip(rows, vectors):
                vector_literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
                cur.execute(
                    """INSERT INTO embeddings(
                           id, owner_type, owner_id, content, embedding, model, created_at, embedding_vector
                       ) VALUES(%s, 'chunk', %s, %s, %s, %s, now(), %s::vector)
                       ON CONFLICT(owner_type, owner_id) DO UPDATE SET
                           content=EXCLUDED.content,
                           embedding=EXCLUDED.embedding,
                           model=EXCLUDED.model,
                           embedding_vector=EXCLUDED.embedding_vector""",
                    (
                        f"EMB-{row['id']}",
                        row["id"],
                        row["content"],
                        json.dumps(vector),
                        embedding_provider.model,
                        vector_literal,
                    ),
                )
        conn.commit()
    return len(rows)


def run_once() -> int:
    """Advance queued/running tasks once.

    The database-backed store is refreshed before scanning so a separate API
    process can enqueue work for this worker. In-memory mode remains useful
    for local development and tests.
    """
    store.refresh()
    candidates = [
        task
        for task in store.tasks.values()
        if task["stage"] in STAGES and task_is_runnable(task)
    ]
    processed = 0
    for task in sorted(candidates, key=lambda item: item["created_at"]):
        claim_token = None
        if store.database:
            claim_token = store.database.claim_task(task["id"])
            if claim_token is None:
                logger.info("task_claim_skipped task_id=%s", task["id"])
                continue
            logger.info("task_claimed task_id=%s", task["id"])
        release_claim = False
        try:
            if claim_token is None:
                advance(task["id"])
            else:
                _advance_with_lease(task["id"], claim_token)
            processed += 1
            release_claim = True
            logger.info("task_processed task_id=%s", task["id"])
        except TaskLeaseLost:
            release_claim = True
            logger.warning("task_lease_lost task_id=%s", task["id"])
        except Exception as exc:
            logger.exception("task_processing_unhandled task_id=%s error_type=%s", task["id"], type(exc).__name__)
        finally:
            if store.database and claim_token is not None and release_claim:
                released = store.database.release_task(task["id"], claim_token)
                logger.info("task_lease_released task_id=%s released=%s", task["id"], released)
            elif store.database and claim_token is not None:
                logger.warning("task_lease_retained_for_recovery task_id=%s", task["id"])
    if candidates:
        logger.info("worker_cycle candidates=%d processed=%d persistence=%s", len(candidates), processed, store.persistence_mode)
    return processed


class _WorkerHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/", "/health"}:
            database_ok = bool(store.database and store.database.ping())
            payload = (
                '{"status":"ok","service":"cognix-nexus-worker","persistence":"postgresql","database":true}'
                if database_ok
                else '{"status":"degraded","service":"cognix-nexus-worker","persistence":"memory-prototype","database":false}'
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args):
        return


def _start_health_server() -> None:
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), _WorkerHealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main() -> None:
    logging.basicConfig(level=os.getenv("COGNIX_WORKER_LOG_LEVEL", "INFO"))
    _start_health_server()
    require_database = os.getenv("COGNIX_REQUIRE_DATABASE", "true" if os.getenv("COGNIX_ENV", "").strip().lower() == "production" else "false").strip().lower() in {"1", "true", "yes", "on"}
    if require_database and store.database is None:
        raise RuntimeError("COGNIX_REQUIRE_DATABASE is enabled but DATABASE_URL is not configured")
    logger.info("worker_started persistence=%s database_configured=%s poll_seconds=%s", store.persistence_mode, bool(store.database), POLL_SECONDS)        finally:
            logger.info("provider_e2e_once_complete run_id=%s", e2e_run_id)
    try:
        while True:
            run_once()
            try:
                books_processed = process_queued_books(limit=2)
                if books_processed:
                    logger.info("book_processing_cycle processed=%d", books_processed)
            except Exception as exc:
                logger.warning("book_processing_cycle_failed error_type=%s", type(exc).__name__)
            try:
                indexed = asyncio.run(_index_unembedded_chunks())
                if indexed:
                    logger.info("embedding_index_cycle indexed=%d model=%s", indexed, embedding_provider.model)
                completed_books = finalize_indexed_books()
                if completed_books:
                    logger.info("book_processing_finalize completed=%d", completed_books)
            except Exception as exc:
                logger.warning("embedding_index_cycle_failed error_type=%s", type(exc).__name__)
            enqueue_due_agent_schedules()
            run_due_agent_jobs()
            _advance_exports()
            time.sleep(POLL_SECONDS)
    finally:
        if store.database:
            store.database.close()


if __name__ == "__main__":
    main()
