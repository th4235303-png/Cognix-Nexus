from __future__ import annotations

"""Phase 21 release checklist evaluation. Evidence is mandatory."""

from dataclasses import dataclass
from .contracts import GateEvidence, GateStatus

@dataclass(frozen=True)
class ReleaseChecklist:
    revision: str
    required_gates: tuple[str, ...]
    evidence: tuple[GateEvidence, ...]

def checklist_status(checklist: ReleaseChecklist) -> GateStatus:
    if not checklist.revision.strip():
        return "blocked"
    by_id = {item.gate_id: item for item in checklist.evidence}
    if any(g not in by_id for g in checklist.required_gates):
        return "pending"
    if any(by_id[g].status != "pass" or not by_id[g].evidence_ref for g in checklist.required_gates):
        return "fail"
    return "pass"
