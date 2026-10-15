"""Phase 17 — Cognix Core Integration runtime.

Exports the shared EvidenceBoundArtifact contract, review gate,
and document assistant / language tutor domain helpers used by the
core_integration_service and router.
"""
from __future__ import annotations

from .contracts import EvidenceBoundArtifact, ready_for_human_review
from .document_assistant import (
    DocumentClassification,
    OCRReview,
    classification_is_valid,
    lifecycle_transition_allowed,
)
from .language_tutor import (
    ParallelText,
    TutorCorrection,
    TutorGoal,
    parallel_text_is_valid,
)

__all__ = [
    # Shared contract
    "EvidenceBoundArtifact",
    "ready_for_human_review",
    # Document assistant
    "DocumentClassification",
    "OCRReview",
    "classification_is_valid",
    "lifecycle_transition_allowed",
    # Language tutor
    "ParallelText",
    "TutorCorrection",
    "TutorGoal",
    "parallel_text_is_valid",
]
