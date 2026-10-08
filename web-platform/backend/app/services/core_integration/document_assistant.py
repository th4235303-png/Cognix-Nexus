from __future__ import annotations

"""Phase 17 Document Assistant deterministic domain contracts."""

from dataclasses import dataclass
from typing import Literal

DocumentType = Literal["contract","letter","form","invoice","receipt","meeting_note","study_material","medical_report","legal_notice","business_card"]

@dataclass(frozen=True)
class DocumentClassification:
    document_type: DocumentType
    confidence: float

@dataclass(frozen=True)
class OCRReview:
    document_id: str
    text: str
    low_confidence_spans: tuple[tuple[int, int], ...]
    review_state: Literal["processing","review","approved","indexed","archived","deleted"]

def classification_is_valid(item: DocumentClassification) -> bool:
    return 0.0 <= item.confidence <= 1.0

def lifecycle_transition_allowed(current: str, target: str) -> bool:
    allowed = {
        "inbox": {"processing"},
        "processing": {"review"},
        "review": {"approved","processing"},
        "approved": {"indexed"},
        "indexed": {"archived","deleted"},
        "archived": {"deleted"},
    }
    return target in allowed.get(current, set())
