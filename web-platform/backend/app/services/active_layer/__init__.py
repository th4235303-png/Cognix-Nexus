"""Phase 13 — AI Active Layer.

Exports stable domain contracts and lifecycle helpers. The runtime
integration (agent.py) uses these types for evidence tracking,
lifecycle fencing, and decision record persistence.
"""
from __future__ import annotations

from .contracts import AgentRun, DecisionRecord, EvidenceRef, Finding
from .events import (
    AgentEventType,
    AgentLifecycleEvent,
    AgentStatus,
    lifecycle_event_is_valid,
    terminal_event_is_fenced,
)
from .execution import ExecutionDecision, ExecutionLease, decide_execution
from .validation import decision_has_evidence, finding_ready_for_review

__all__ = [
    # Contracts
    "AgentRun",
    "DecisionRecord",
    "EvidenceRef",
    "Finding",
    # Events
    "AgentEventType",
    "AgentLifecycleEvent",
    "AgentStatus",
    "lifecycle_event_is_valid",
    "terminal_event_is_fenced",
    # Execution
    "ExecutionDecision",
    "ExecutionLease",
    "decide_execution",
    # Validation
    "decision_has_evidence",
    "finding_ready_for_review",
]