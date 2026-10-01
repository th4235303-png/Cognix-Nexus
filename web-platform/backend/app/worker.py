from __future__ import annotations

import os
import time
from app.services.agent import enqueue_due_agent_schedules, run_due_agent_jobs
from app.services.export_worker import advance_export_job

from app.services.processing import STAGES, advance
from app.store import store


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
    return processed


def main() -> None:
    while True:
        run_once()
        enqueue_due_agent_schedules()
        run_due_agent_jobs()
        _advance_exports()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
