from __future__ import annotations

"""Phase 17 — Cognix Core Integration runtime service helpers.

Invariants:
  1. EvidenceBoundArtifact must have evidence before review transition.
  2. Document lifecycle transitions follow the allowed-state machine only.
  3. ParallelText requires both source and translation non-empty and different languages.
  4. TutorGoal framework must be a known standard (CEFR, JLPT, TOPIK).
  5. All artifacts are owner-isolated and fail-closed.
  6. No artifact becomes canonical without human review (ready_for_human_review gate).
"""

import json
from uuid import uuid4

from app.store import store
from app.services.core_integration import (
    EvidenceBoundArtifact,
    ready_for_human_review,
    DocumentClassification,
    OCRReview,
    classification_is_valid,
    lifecycle_transition_allowed,
    ParallelText,
    TutorCorrection,
    TutorGoal,
    parallel_text_is_valid,
)
from app.services.active_layer.contracts import EvidenceRef

_ARTIFACT_TYPES = frozenset({
    "claim", "translation", "fact_check", "research_report",
    "document", "ocr_review", "parallel_text", "tutor_correction",
})
_TUTOR_FRAMEWORKS = frozenset({"CEFR", "JLPT", "TOPIK"})
_DOC_LIFECYCLE_STATES = frozenset({
    "inbox", "processing", "review", "approved", "indexed", "archived", "deleted",
})


# ─── persist_evidence_artifact ────────────────────────────────────────────────

def persist_evidence_artifact(
    owner_id: str,
    artifact_type: str,
    evidence_refs: list[dict],
    payload: dict,
) -> str | None:
    """Persist a Phase 17 EvidenceBoundArtifact (needs_review state).

    Invariants:
      - evidence_refs must be non-empty (fail-closed)
      - artifact_type must be a known type
      - owner_id must be non-empty
    Returns artifact ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip():
        return None
    if artifact_type not in _ARTIFACT_TYPES:
        return None
    if not evidence_refs:
        return None

    artifact_id = f"CART-{uuid4().hex[:8].upper()}"
    evidence_tuple = tuple(
        EvidenceRef(
            source_type=str(e.get("source_type", "chunk")),
            source_id=str(e.get("source_id", "")),
            locator=e.get("locator"),
            excerpt=e.get("excerpt"),
        )
        for e in evidence_refs[:20]
    )
    artifact = EvidenceBoundArtifact(
        id=artifact_id,
        artifact_type=artifact_type,
        owner_id=owner_id,
        evidence=evidence_tuple,
        review_state="needs_review",
    )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO core_artifacts"
                "(id, owner_id, artifact_type, evidence_refs, payload, review_state) "
                "VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, 'needs_review') RETURNING id",
                (
                    artifact.id, owner_id, artifact_type,
                    json.dumps(evidence_refs),
                    json.dumps(payload),
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_document_classification ─────────────────────────────────────────

def persist_document_classification(
    owner_id: str,
    document_id: str,
    document_type: str,
    confidence: float,
) -> str | None:
    """Persist a document classification. confidence must be in [0, 1]."""
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not document_id.strip():
        return None

    classification = DocumentClassification(
        document_type=document_type,  # type: ignore[arg-type]
        confidence=confidence,
    )
    if not classification_is_valid(classification):
        return None

    cls_id = f"DCLS-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO core_document_classifications"
                "(id, owner_id, document_id, document_type, confidence) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (cls_id, owner_id, document_id, document_type, float(confidence)),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── apply_document_lifecycle_transition ──────────────────────────────────────

def apply_document_lifecycle_transition(
    owner_id: str,
    document_id: str,
    current_state: str,
    target_state: str,
) -> bool:
    """Attempt a document lifecycle state transition using the state machine.

    Returns True if the transition was applied, False if not allowed or DB unavailable.
    """
    db = store.database
    if db is None:
        return False
    if not owner_id.strip() or not document_id.strip():
        return False
    if not lifecycle_transition_allowed(current_state, target_state):
        return False

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE core_documents SET lifecycle_state = %s, updated_at = now() "
                "WHERE id = %s AND owner_id = %s AND lifecycle_state = %s",
                (target_state, document_id, owner_id, current_state),
            )
            updated = cur.rowcount
        conn.commit()
    return updated > 0


# ─── persist_parallel_text ────────────────────────────────────────────────────

def persist_parallel_text(
    owner_id: str,
    source_language: str,
    target_language: str,
    source: str,
    translation: str,
    reading: str | None = None,
) -> str | None:
    """Persist a ParallelText. Validates source != target language and both non-empty."""
    db = store.database
    if db is None:
        return None
    if not owner_id.strip():
        return None

    pt = ParallelText(
        source_language=source_language,  # type: ignore[arg-type]
        target_language=target_language,  # type: ignore[arg-type]
        source=source,
        translation=translation,
        reading=reading,
    )
    if not parallel_text_is_valid(pt):
        return None

    pt_id = f"PTXT-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO core_parallel_texts"
                "(id, owner_id, source_language, target_language, source, translation, reading) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (pt_id, owner_id, source_language, target_language,
                 source[:5000], translation[:5000], reading),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None
