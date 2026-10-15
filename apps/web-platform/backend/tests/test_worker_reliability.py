from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from app.services.lease_runner import LeaseLostError, run_with_lease_heartbeat
from app.services.task_retry import (
    MAX_PROCESSING_RETRIES,
    retry_delay_seconds,
    retry_ready,
    task_is_runnable,
)


class WorkerRetryPolicyTests(unittest.TestCase):
    def test_retry_delay_is_exponential_and_capped(self):
        self.assertEqual(
            [retry_delay_seconds(count) for count in range(7)],
            [0, 5, 10, 20, 40, 80, 160],
        )
        self.assertEqual(retry_delay_seconds(MAX_PROCESSING_RETRIES + 2), 300)

    def test_retry_readiness_uses_injected_time_without_sleeping(self):
        task = {
            "status": "queued",
            "retry_count": 2,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertFalse(retry_ready(task, start.replace(second=9)))
        self.assertTrue(retry_ready(task, start.replace(second=10)))
        self.assertTrue(retry_ready({**task, "status": "running"}, start))

    def test_terminal_and_review_tasks_are_not_runnable(self):
        task = {
            "status": "completed",
            "stage": "needs_review",
            "retry_count": 0,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        self.assertFalse(task_is_runnable(task))
        self.assertFalse(task_is_runnable({**task, "status": "failed", "stage": "extracting"}))
        self.assertTrue(task_is_runnable({**task, "status": "running", "stage": "extracting"}))

    def test_lost_lease_stops_work_before_persistence(self):
        class ImmediateEvent:
            def __init__(self):
                self.value = False

            def set(self):
                self.value = True

            def is_set(self):
                return self.value

            def wait(self, _timeout):
                return self.value

        class ImmediateThread:
            def __init__(self, target, daemon):
                self.target = target

            def start(self):
                self.target()

            def join(self):
                return None

        persisted = []

        def work(lease_is_valid):
            if not lease_is_valid():
                raise LeaseLostError("lease lost before persistence")
            persisted.append(True)

        with (
            patch("app.services.lease_runner.threading.Thread", ImmediateThread),
            patch("app.services.lease_runner.threading.Event", ImmediateEvent),
        ):
            with self.assertRaises(LeaseLostError):
                run_with_lease_heartbeat(
                    "test_job",
                    "test-id",
                    lambda: False,
                    work,
                )
        self.assertEqual(persisted, [])


if __name__ == "__main__":
    unittest.main()
