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

from app.services.processing import STAGES, advance
from app.store import store


logger = logging.getLogger("cognix.worker")

POLL_SECONDS = float(os.getenv("COGNIX_WORKER_POLL_SECONDS", "2"))


def _advance_exports(limit: int = 5) -> int:
    store.refresh()
    processed = 0
    for job in list(store.exports.values()):
        if processed >= limit:
            break
        if job["status"] not in {"queued", "uploading"}:
            continue
        try:
            advance_export_job(job["id"])
            processed += 1
        except Exception:
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
        if task["status"] in {"queued", "running"}
        and task["stage"] in STAGES
        and task["stage"] not in {"needs_review", "approved"}
    ]
    processed = 0
    for task in sorted(candidates, key=lambda item: item["created_at"]):
        if store.database and not store.database.try_claim_task(task["id"]):
            continue
        try:
            advance(task["id"])
            processed += 1
        finally:
            if store.database:
                store.database.release_task(task["id"])
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
    require_database = os.getenv("COGNIX_REQUIRE_DATABASE", "false").strip().lower() in {"1", "true", "yes", "on"}
    if require_database and store.database is None:
        raise RuntimeError("COGNIX_REQUIRE_DATABASE is enabled but DATABASE_URL is not configured")
    logger.info("worker_started persistence=%s database_configured=%s poll_seconds=%s", store.persistence_mode, bool(store.database), POLL_SECONDS)
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


if __name__ == "__main__":
    main()
