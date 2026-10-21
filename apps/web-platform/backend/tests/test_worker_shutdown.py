from __future__ import annotations

import signal
import threading

from app import worker


def test_sigterm_requests_worker_shutdown(monkeypatch):
    requested = threading.Event()
    monkeypatch.setattr(worker, "SHUTDOWN_REQUESTED", requested)

    worker._request_shutdown(signal.SIGTERM, None)

    assert requested.is_set()
