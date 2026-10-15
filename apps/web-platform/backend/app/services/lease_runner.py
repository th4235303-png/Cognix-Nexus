from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


class LeaseLostError(RuntimeError):
    pass


def run_with_lease_heartbeat(
    job_type: str,
    job_id: str,
    renew: Callable[[], bool],
    work: Callable[[Callable[[], bool]], T],
    interval_seconds: int = 300,
) -> T:
    lost = threading.Event()
    stop = threading.Event()
    logger = logging.getLogger("cognix.worker")

    def heartbeat() -> None:
        while not stop.wait(interval_seconds):
            try:
                if not renew():
                    lost.set()
                    logger.warning("%s_lease_renewal_lost job_id=%s", job_type, job_id)
                    return
            except Exception as exc:
                lost.set()
                logger.exception(
                    "%s_lease_renewal_failed job_id=%s error_type=%s",
                    job_type,
                    job_id,
                    type(exc).__name__,
                )
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        result = work(lambda: not lost.is_set())
        if lost.is_set():
            raise LeaseLostError(f"{job_type} lease lost for {job_id}")
        return result
    finally:
        stop.set()
        thread.join()
