from __future__ import annotations

import sitecustomize  # noqa: F401,E402 — apply psycopg pooler compatibility before app imports
import asyncio
import logging
import os
import signal
import threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app.services.embeddings import embedding_provider
from app.services.agent import enqueue_due_agent_schedules, run_due_agent_jobs
from app.services.export_worker import advance_export_job
from app.services.book_processing import process_queued_books, finalize_indexed_books
from app.services.book_intelligence import advance_book_ai

from app.services.processing import STAGES, TaskLeaseLost, advance
from app.services.task_retry import task_is_runnable
from app.store import store


logger = logging.getLogger("cognix.worker")

POLL_SECONDS = float(os.getenv("COGNIX_WORKER_POLL_SECONDS", "2"))
LEASE_HEARTBEAT_SECONDS = 5 * 60
SHUTDOWN_REQUESTED = threading.Event()


def _request_shutdown(signum: int, _frame) -> None:
    """Stop claiming new work and let the current unit of work finish."""
    logger.info("worker_shutdown_requested signal=%s", signum)
    SHUTDOWN_REQUESTED.set()


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
    if SHUTDOWN_REQUESTED.is_set():
        logger.info("worker_shutdown_skipping_cycle")
        return 0
    store.refresh()
    candidates = [
        task
        for task in store.tasks.values()
        if task["stage"] in STAGES and task["status"] in {"queued", "running"} and task_is_runnable(task)
    ]
    processed = 0
    for task in sorted(candidates, key=lambda item: (item["updated_at"], item["created_at"]), reverse=True):
        if SHUTDOWN_REQUESTED.is_set():
            logger.info("worker_shutdown_stopping_new_tasks")
            break
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
            payload = json.dumps(
                {
                    "status": "ok" if database_ok else "degraded",
                    "service": "cognix-nexus-worker",
                    "persistence": "postgresql" if database_ok else "memory-prototype",
                    "database": database_ok,
                    "revision": os.getenv("RENDER_GIT_COMMIT", "").strip() or "unknown",
                },
                separators=(",", ":"),
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


def _start_health_server() -> ThreadingHTTPServer:
    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), _WorkerHealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> None:
    logging.basicConfig(level=os.getenv("COGNIX_WORKER_LOG_LEVEL", "INFO"))
    SHUTDOWN_REQUESTED.clear()
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)
    health_server = _start_health_server()
    try:
        require_database = os.getenv("COGNIX_REQUIRE_DATABASE", "true" if os.getenv("COGNIX_ENV", "").strip().lower() == "production" else "false").strip().lower() in {"1", "true", "yes", "on"}
        if require_database and store.database is None:
            raise RuntimeError("COGNIX_REQUIRE_DATABASE is enabled but DATABASE_URL is not configured")
        logger.info("worker_started persistence=%s database_configured=%s poll_seconds=%s", store.persistence_mode, bool(store.database), POLL_SECONDS)
        while not SHUTDOWN_REQUESTED.is_set():
            run_once()
            if SHUTDOWN_REQUESTED.is_set():
                break
            try:
                books_processed = process_queued_books(limit=2)
                if books_processed:
                    logger.info("book_processing_cycle processed=%d", books_processed)
            except Exception as exc:
                logger.warning("book_processing_cycle_failed error_type=%s", type(exc).__name__)
            if SHUTDOWN_REQUESTED.is_set():
                break
            try:
                indexed = asyncio.run(_index_unembedded_chunks())
                if indexed:
                    logger.info("embedding_index_cycle indexed=%d model=%s", indexed, embedding_provider.model)
                completed_books = finalize_indexed_books()
                ai_books = asyncio.run(advance_book_ai(limit=1))
                if ai_books:
                    logger.info("book_ai_cycle processed=%d", ai_books)
                if completed_books:
                    logger.info("book_processing_finalize completed=%d", completed_books)
            except Exception as exc:
                logger.warning("embedding_index_cycle_failed error_type=%s", type(exc).__name__)
            if SHUTDOWN_REQUESTED.is_set():
                break
            enqueue_due_agent_schedules()
            if SHUTDOWN_REQUESTED.is_set():
                break
            run_due_agent_jobs()
            if SHUTDOWN_REQUESTED.is_set():
                break
            _advance_exports()
            SHUTDOWN_REQUESTED.wait(max(0.0, POLL_SECONDS))
    finally:
        health_server.shutdown()
        health_server.server_close()
        if store.database:
            store.database.close()


if __name__ == "__main__":
    main()
