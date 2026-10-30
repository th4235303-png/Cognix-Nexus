from __future__ import annotations

import sitecustomize  # noqa: F401,E402 — apply psycopg pooler compatibility before app imports
import asyncio
import base64
import hashlib
import hmac
import logging
import os
import signal
import threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
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
                logger.exception("task_lease_renewal_failed task_id=%s error_type=%s", task_id, type(exc).__name__)
                return

    heartbeat = threading.Thread(target=renew_lease, daemon=True)
    heartbeat.start()
    try:
        return advance(task_id, claim_token=claim_token, lease_is_valid=lambda: not lost.is_set())
    finally:
        stop.set()
        heartbeat.join()


def _process_task(task_id: str) -> bool:
    store.refresh()
    task = store.tasks.get(task_id)
    if not task or task.get("status") not in {"queued", "running"} or not task_is_runnable(task):
        return False
    claim_token = store.database.claim_task(task_id) if store.database else None
    if store.database and claim_token is None:
        return False
    try:
        if claim_token is None:
            advance(task_id)
        else:
            _advance_with_lease(task_id, claim_token)
        logger.info("qstash_task_processed task_id=%s", task_id)
        return True
    except Exception as exc:
        logger.exception("qstash_task_processing_failed task_id=%s error_type=%s", task_id, type(exc).__name__)
        return False
    finally:
        if store.database and claim_token is not None:
            store.database.release_task(task_id, claim_token)


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
            logger.exception("export_job_processing_failed export_id=%s error_type=%s", job["id"], type(exc).__name__)
            continue
    return processed


async def _index_unembedded_chunks(limit: int = 25) -> int:
    if not store.database or not embedding_provider.configured:
        return 0
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT c.id, c.content
                   FROM chunks c
                   LEFT JOIN embeddings e ON e.owner_type='chunk' AND e.owner_id=c.id
                   WHERE e.owner_id IS NULL
                   ORDER BY c.created_at
                   LIMIT %s""", (limit,))
            rows = cur.fetchall()
    if not rows:
        return 0
    vectors = await embedding_provider.embed([row["content"] for row in rows])
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            for row, vector in zip(rows, vectors):
                vector_literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
                cur.execute("""INSERT INTO embeddings(
                           id, owner_type, owner_id, content, embedding, model, created_at, embedding_vector
                       ) VALUES(%s, 'chunk', %s, %s, %s, %s, now(), %s::vector)
                       ON CONFLICT(owner_type, owner_id) DO UPDATE SET
                           content=EXCLUDED.content,
                           embedding=EXCLUDED.embedding,
                           model=EXCLUDED.model,
                           embedding_vector=EXCLUDED.embedding_vector""", (
                    f"EMB-{row['id']}", row["id"], row["content"], json.dumps(vector), embedding_provider.model, vector_literal,
                ))
        conn.commit()
    return len(rows)


def run_once() -> int:
    if SHUTDOWN_REQUESTED.is_set():
        logger.info("worker_shutdown_skipping_cycle")
        return 0
    store.refresh()
    candidates = [task for task in store.tasks.values() if task["stage"] in STAGES and task["status"] in {"queued", "running"} and task_is_runnable(task)]
    processed = 0
    for task in sorted(candidates, key=lambda item: (item["updated_at"], item["created_at"]), reverse=True):
        if SHUTDOWN_REQUESTED.is_set():
            break
        if _process_task(task["id"]):
            processed += 1
    if candidates:
        logger.info("worker_cycle candidates=%d processed=%d persistence=%s", len(candidates), processed, store.persistence_mode)
    return processed


def _verify_qstash_request(signature: str, raw_body: bytes) -> bool:
    """Verify QStash's signed JWT, destination URL, and raw-body hash."""
    current_key = os.getenv("QSTASH_CURRENT_SIGNING_KEY", "").strip()
    next_key = os.getenv("QSTASH_NEXT_SIGNING_KEY", "").strip()
    destination = os.getenv("QSTASH_CALLBACK_URL", "").strip()
    if not signature or not destination or not current_key or not next_key:
        return False
    expected_body = base64.urlsafe_b64encode(hashlib.sha256(raw_body).digest()).decode("ascii").rstrip("=")
    for signing_key in (current_key, next_key):
        try:
            claims = jwt.decode(signature, signing_key, algorithms=["HS256"], issuer="Upstash", leeway=10)
        except jwt.PyJWTError:
            continue
        body_claim = claims.get("body")
        if claims.get("sub") == destination and isinstance(body_claim, str):
            if hmac.compare_digest(body_claim.rstrip("="), expected_body):
                return True
    return False


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
                    "queue": "qstash+redis" if os.getenv("QSTASH_CURRENT_SIGNING_KEY") and os.getenv("QSTASH_NEXT_SIGNING_KEY") and os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN") else "postgres-poll",
                    "revision": os.getenv("RENDER_GIT_COMMIT", "").strip() or "unknown",
                },
                separators=(",", ":"),
            ).encode("utf-8")
            self.send_response(200 if database_ok else 503)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/qstash/process":
            self.send_response(404)
            self.end_headers()
            return
        if not all(os.getenv(name, "").strip() for name in ("QSTASH_CURRENT_SIGNING_KEY", "QSTASH_NEXT_SIGNING_KEY", "QSTASH_CALLBACK_URL")):
            self.send_response(503)
            self.end_headers()
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            raw_body = self.rfile.read(length)
            signature = self.headers.get("Upstash-Signature", "")
            if not _verify_qstash_request(signature, raw_body):
                self.send_response(401)
                self.end_headers()
                return
            payload = json.loads(raw_body or b"{}")
            task_id = str(payload.get("task_id", "")).strip()
            if not task_id:
                self.send_response(400)
                self.end_headers()
                return
            ok = _process_task(task_id)
            body = json.dumps({"status": "processed" if ok else "skipped", "task_id": task_id}).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            logger.exception("qstash_callback_failed error_type=%s", type(exc).__name__)
            self.send_response(500)
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
            if SHUTDOWN_REQUESTED.is_set(): break
            try:
                books_processed = process_queued_books(limit=2)
                if books_processed: logger.info("book_processing_cycle processed=%d", books_processed)
            except Exception as exc:
                logger.warning("book_processing_cycle_failed error_type=%s", type(exc).__name__)
            if SHUTDOWN_REQUESTED.is_set(): break
            try:
                indexed = asyncio.run(_index_unembedded_chunks())
                if indexed: logger.info("embedding_index_cycle indexed=%d model=%s", indexed, embedding_provider.model)
                completed_books = finalize_indexed_books()
                ai_books = asyncio.run(advance_book_ai(limit=1))
                if ai_books: logger.info("book_ai_cycle processed=%d", ai_books)
                if completed_books: logger.info("book_processing_finalize completed=%d", completed_books)
            except Exception as exc:
                logger.warning("embedding_index_cycle_failed error_type=%s", type(exc).__name__)
            if SHUTDOWN_REQUESTED.is_set(): break
            enqueue_due_agent_schedules()
            if SHUTDOWN_REQUESTED.is_set(): break
            run_due_agent_jobs()
            if SHUTDOWN_REQUESTED.is_set(): break
            _advance_exports()
            SHUTDOWN_REQUESTED.wait(max(0.0, POLL_SECONDS))
    finally:
        health_server.shutdown()
        health_server.server_close()
        if store.database:
            store.database.close()


if __name__ == "__main__":
    main()
