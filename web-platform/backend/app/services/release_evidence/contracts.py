from __future__ import annotations

"""Non-runtime Phase 20/21 release evidence contracts."""

from dataclasses import dataclass
from typing import Literal


GateStatus = Literal["pending", "pass", "fail", "blocked"]


@dataclass(frozen=True)
class GateEvidence:
    gate_id: str
    status: GateStatus
    evidence_ref: str | None = None
    observed_at: str | None = None


@dataclass(frozen=True)
class ReleaseDecision:
    revision: str
    approved: bool
    required_gate_ids: tuple[str, ...]
    evidence: tuple[GateEvidence, ...]


def release_is_ready(decision: ReleaseDecision) -> bool:
    if not decision.revision.strip() or not decision.approved:
        return False
    by_id = {item.gate_id: item for item in decision.evidence}
    return all(
        gate_id in by_id
        and by_id[gate_id].status == "pass"
        and bool(by_id[gate_id].evidence_ref)
        for gate_id in decision.required_gate_ids
    )
