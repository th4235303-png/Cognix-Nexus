from __future__ import annotations

"""Non-runtime lifecycle contracts for the Phase 13 durable execution boundary."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


AgentStatus = Literal["queued", "running", "paused", "completed", "failed", "cancelled"]
AgentEventType = Literal[
    "queued",
    "started",
    "paused",
    "resumed",
    "completed",
    "failed",
    "cancelled",
    "retry_scheduled",
]


@dataclass(frozen=True)
class AgentLifecycleEvent:
    run_id: str
    owner_id: str
    event_type: AgentEventType
    occurred_at: datetime
    idempotency_key: str


_TERMINAL = {"completed", "failed", "cancelled"}


def lifecycle_event_is_valid(event: AgentLifecycleEvent) -> bool:
    return bool(
        event.run_id.strip()
        and event.owner_id.strip()
        and event.idempotency_key.strip()
    )


def terminal_event_is_fenced(current_status: AgentStatus, event_type: AgentEventType) -> bool:
    """Reject mutations that would revive a terminal run."""
    return current_status in _TERMINAL and event_type not in {"completed", "failed", "cancelled"}
