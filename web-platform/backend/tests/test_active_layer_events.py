import unittest
from datetime import datetime, timezone

from app.services.active_layer.events import (
    AgentLifecycleEvent,
    lifecycle_event_is_valid,
    terminal_event_is_fenced,
)


class ActiveLayerLifecycleEventTests(unittest.TestCase):
    def test_event_requires_owner_run_and_idempotency_key(self):
        event = AgentLifecycleEvent(
            run_id="run-1",
            owner_id="owner-1",
            event_type="started",
            occurred_at=datetime.now(timezone.utc),
            idempotency_key="run-1:started",
        )
        self.assertTrue(lifecycle_event_is_valid(event))
        self.assertFalse(
            lifecycle_event_is_valid(
                AgentLifecycleEvent(
                    run_id="",
                    owner_id="owner-1",
                    event_type="started",
                    occurred_at=event.occurred_at,
                    idempotency_key="run-1:started",
                )
            )
        )

    def test_terminal_run_cannot_be_revived(self):
        self.assertTrue(terminal_event_is_fenced("completed", "started"))
        self.assertTrue(terminal_event_is_fenced("failed", "resumed"))
        self.assertFalse(terminal_event_is_fenced("running", "completed"))


if __name__ == "__main__":
    unittest.main()
