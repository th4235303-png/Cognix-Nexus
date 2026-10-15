from __future__ import annotations

from dataclasses import dataclass
from app.services.active_layer.contracts import EvidenceRef

@dataclass(frozen=True)
class EvidenceBoundArtifact:
    id: str
    artifact_type: str
    owner_id: str
    evidence: tuple[EvidenceRef, ...] = ()
    review_state: str = "draft"

def ready_for_human_review(artifact: EvidenceBoundArtifact) -> bool:
    return bool(artifact.owner_id and artifact.evidence and artifact.review_state == "needs_review")
