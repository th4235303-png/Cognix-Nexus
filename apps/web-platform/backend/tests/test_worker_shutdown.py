from __future__ import annotations

import signal
import threading

from app import worker


def test_sigterm_requests_worker_shutdown(monkeypatch):
    requested = threading.Event()
    monkeypatch.setattr(worker, "SHUTDOWN_REQUESTED", requested)

    worker._request_shutdown(signal.SIGTERM, None)

    assert requested.is_set()


def test_run_once_skips_queue_scan_after_shutdown(monkeypatch):
    requested = threading.Event()
    requested.set()
    monkeypatch.setattr(worker, "SHUTDOWN_REQUESTED", requested)

    class FakeStore:
        database = None
        persistence_mode = "memory-prototype"
        tasks = {"task-1": {"id": "task-1", "status": "queued"}}

        def refresh(self):
            raise AssertionError("shutdown should skip the queue scan")

    monkeypatch.setattr(worker, "store", FakeStore())

    def unexpected_advance(*_args, **_kwargs):
        raise AssertionError("shutdown should not advance a task")

    monkeypatch.setattr(worker, "advance", unexpected_advance)

    assert worker.run_once() == 0


def test_run_once_does_not_start_next_task_after_shutdown(monkeypatch):
    requested = threading.Event()
    monkeypatch.setattr(worker, "SHUTDOWN_REQUESTED", requested)
    stage = next(stage for stage in worker.STAGES if stage not in {"needs_review", "approved"})
    timestamp = "2026-10-21T00:00:00+00:00"

    class FakeStore:
        database = None
        persistence_mode = "memory-prototype"
        tasks = {
            "task-1": {
                "id": "task-1",
                "status": "queued",
                "stage": stage,
                "retry_count": 0,
                "updated_at": timestamp,
                "created_at": timestamp,
            },
            "task-2": {
                "id": "task-2",
                "status": "queued",
                "stage": stage,
                "retry_count": 0,
                "updated_at": timestamp,
                "created_at": timestamp,
            },
        }

        def refresh(self):
            return None

    monkeypatch.setattr(worker, "store", FakeStore())
    advanced = []

    def advance_one(task_id):
        advanced.append(task_id)
        requested.set()
        return {}

    monkeypatch.setattr(worker, "advance", advance_one)

    assert worker.run_once() == 1
    assert len(advanced) == 1
