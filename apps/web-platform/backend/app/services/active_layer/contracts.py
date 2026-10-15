from __future__ import annotations

"""Provider-agnostic Phase 13 domain contracts."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class EvidenceRef:
    source_type: str
    source_id: str
    locator: str | None = None
    excerpt: str | None = None


@dataclass(frozen=True)
class Finding:
    id: str
    statement: str
    evidence: tuple[EvidenceRef, ...] = ()
    confidence: float | None = None
    review_state: Literal["draft", "needs_review", "approved", "rejected"] = "draft"


@dataclass(frozen=True)
class AgentRun:
    id: str
    goal: str
    status: Literal["queued", "running", "paused", "completed", "failed", "cancelled"] = "queued"
    evidence: tuple[EvidenceRef, ...] = ()
    findings: tuple[Finding, ...] = ()
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionRecord:
    id: str
    decision: str
    rationale: str
    evidence: tuple[EvidenceRef, ...] = ()
    approved_by: str | None = None
