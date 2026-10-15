from __future__ import annotations

"""Phase 14 deterministic planning helpers. No scheduler side effects."""

from dataclasses import dataclass
from .contracts import LearningPathItem, decay_weight

@dataclass(frozen=True)
class LearningCandidate:
    subject_id: str
    weakness: float
    age_days: float
    half_life_days: float
    evidence_refs: tuple[str, ...] = ()

def priority(candidate: LearningCandidate) -> float:
    if not candidate.subject_id.strip():
        raise ValueError("subject_id is required")
    return max(0.0, candidate.weakness) * decay_weight(candidate.age_days, candidate.half_life_days)

def build_path(candidates: tuple[LearningCandidate, ...], limit: int) -> tuple[LearningPathItem, ...]:
    if limit <= 0:
        return ()
    ranked = sorted(candidates, key=priority, reverse=True)[:limit]
    return tuple(
        LearningPathItem(str(i + 1), c.subject_id, i, "weakness×decay priority", c.evidence_refs)
        for i, c in enumerate(ranked)
    )
