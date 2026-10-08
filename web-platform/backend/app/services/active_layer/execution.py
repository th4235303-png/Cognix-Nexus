from __future__ import annotations

"""Phase 13 deterministic execution-boundary helpers. No production activation."""

from dataclasses import dataclass
from typing import Literal

from .events import AgentStatus, AgentEventType, terminal_event_is_fenced

@dataclass(frozen=True)
class ExecutionLease:
    run_id: str
    owner_id: str
    lease_id: str
    attempt: int
    heartbeat_at: str
    expires_at: str

@dataclass(frozen=True)
class ExecutionDecision:
    action: Literal["start", "resume", "retry", "ignore", "reject"]
    reason: str

def decide_execution(current_status: AgentStatus, event_type: AgentEventType, idempotency_seen: bool) -> ExecutionDecision:
    if terminal_event_is_fenced(current_status, event_type):
        return ExecutionDecision("reject", "terminal run cannot be revived")
    if idempotency_seen:
        return ExecutionDecision("ignore", "duplicate idempotency key")
    if event_type in {"started", "resumed"}:
        return ExecutionDecision("start" if current_status == "queued" else "resume", "lifecycle transition accepted")
    if event_type == "retry_scheduled":
        return ExecutionDecision("retry", "retry is explicitly scheduled")
    return ExecutionDecision("start", "non-terminal lifecycle event accepted")
