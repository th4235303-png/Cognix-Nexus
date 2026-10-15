from __future__ import annotations

"""Provider-agnostic Phase 14 learning-science contracts."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class LearningSignal:
    id: str
    subject_id: str
    signal_type: Literal["review", "recall", "completion", "difficulty", "reflection"]
    strength: float
    occurred_at: str
    evidence_refs: tuple[str, ...] = ()

@dataclass(frozen=True)
class LearningPathItem:
    id: str
    subject_id: str
    position: int
    reason: str
    evidence_refs: tuple[str, ...] = ()

def decay_weight(age_days: float, half_life_days: float) -> float:
    if age_days < 0:
        raise ValueError("age_days must be non-negative")
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    return 0.5 ** (age_days / half_life_days)
