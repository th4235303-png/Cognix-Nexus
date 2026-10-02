from __future__ import annotations

import logging
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app.services.agent import enqueue_due_agent_schedules, run_due_agent_jobs
from app.services.export_worker import advance_export_job

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
                '{"status":"ok","service":"cognix-core-worker","persistence":"postgresql","database":true}'
                if database_ok
                else '{"status":"degraded","service":"cognix-core-worker","persistence":"memory-prototype","database":false}'
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
    logger.info("worker_started persistence=%s database_configured=%s poll_seconds=%s", store.persistence_mode, bool(store.database), POLL_SECONDS)
    while True:
        run_once()
        enqueue_due_agent_schedules()
        run_due_agent_jobs()
        _advance_exports()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
