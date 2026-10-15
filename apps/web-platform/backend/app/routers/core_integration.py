from __future__ import annotations

"""Phase 17 — Cognix Core Integration API router.

Endpoints:
  POST   /core/artifacts                    Create an evidence-bound artifact
  GET    /core/artifacts                    List artifacts (optionally filter by type)
  PATCH  /core/artifacts/{id}/review        Approve or reject an artifact

  POST   /core/documents                    Register a document (inbox state)
  GET    /core/documents                    List documents
  PATCH  /core/documents/{id}/transition    Apply lifecycle state transition (state machine)
  POST   /core/documents/{id}/classify      Record a classification for a document

  POST   /core/translations                 Persist a parallel text translation
  GET    /core/translations                 List parallel texts

Phase 17 invariants preserved:
  1. No artifact becomes canonical without human review (ready_for_human_review gate).
  2. Evidence refs must be attached to every artifact.
  3. Document transitions follow the allowed state machine only.
  4. ParallelText requires source != target language and both non-empty.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.ownership import owner_for_request
from app.store import store
from app.services.core_integration_service import (
    persist_evidence_artifact,
    persist_document_classification,
    apply_document_lifecycle_transition,
    persist_parallel_text,
)
from app.services.core_integration import lifecycle_transition_allowed

router = APIRouter(prefix="/core", tags=["core-integration"])

_ARTIFACT_TYPES = {
    "claim","translation","fact_check","research_report",
    "document","ocr_review","parallel_text","tutor_correction",
}
_LANGUAGES = {"my", "ja", "ko"}


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for Core Integration")
    return store.database


# ─── Pydantic models ──────────────────────────────────────────────────────────

class ArtifactCreate(BaseModel):
    artifact_type: str = Field(pattern=r"^(claim|translation|fact_check|research_report|document|ocr_review|parallel_text|tutor_correction)$")
    evidence_refs: list[dict] = Field(min_length=1, description="Evidence refs — at least 1 required")
    payload: dict = Field(default_factory=dict)

    @field_validator("evidence_refs")
    @classmethod
    def evidence_non_empty(cls, v: list[dict]) -> list[dict]:
        if not v:
            raise ValueError("evidence_refs must have at least one entry")
        return v


class ArtifactReview(BaseModel):
    review_state: str = Field(pattern=r"^(approved|rejected)$")


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source_ref: str | None = Field(default=None, max_length=2000)


class DocumentTransition(BaseModel):
    current_state: str
    target_state: str


class DocumentClassify(BaseModel):
    document_type: str = Field(
        pattern=r"^(contract|letter|form|invoice|receipt|meeting_note|study_material|medical_report|legal_notice|business_card)$"
    )
    confidence: float = Field(ge=0.0, le=1.0)


class ParallelTextCreate(BaseModel):
    source_language: str = Field(pattern=r"^(my|ja|ko)$")
    target_language: str = Field(pattern=r"^(my|ja|ko)$")
    source: str = Field(min_length=1, max_length=5000)
    translation: str = Field(min_length=1, max_length=5000)
    reading: str | None = Field(default=None, max_length=1000)

    @field_validator("target_language")
    @classmethod
    def languages_must_differ(cls, v: str, info) -> str:
        src = info.data.get("source_language")
        if src and v == src:
            raise ValueError("source_language and target_language must be different")
        return v


# ─── Artifact endpoints ───────────────────────────────────────────────────────

@router.post("/artifacts", status_code=201)
def create_artifact(payload: ArtifactCreate, request: Request) -> dict:
    """Create an evidence-bound artifact — evidence required, starts in needs_review."""
    db = _db()
    owner_id = owner_for_request(request)

    artifact_id = persist_evidence_artifact(
        owner_id=owner_id,
        artifact_type=payload.artifact_type,
        evidence_refs=payload.evidence_refs,
        payload=payload.payload,
    )
    if artifact_id is None:
        raise HTTPException(status_code=422, detail="Artifact could not be created — validation failed")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM core_artifacts WHERE id = %s AND owner_id = %s", (artifact_id, owner_id))
            return cur.fetchone()


@router.get("/artifacts")
def list_artifacts(request: Request, artifact_type: str | None = None, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if artifact_type:
                cur.execute(
                    "SELECT * FROM core_artifacts WHERE owner_id = %s AND artifact_type = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, artifact_type, limit))
            else:
                cur.execute(
                    "SELECT * FROM core_artifacts WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.patch("/artifacts/{artifact_id}/review")
def review_artifact(artifact_id: str, payload: ArtifactReview, request: Request) -> dict:
    """Approve or reject an artifact. Only 'needs_review' artifacts can be reviewed."""
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE core_artifacts SET review_state = %s, reviewed_at = now(), updated_at = now() "
                "WHERE id = %s AND owner_id = %s AND review_state = 'needs_review' RETURNING *",
                (payload.review_state, artifact_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found or already reviewed")
    return row


# ─── Document endpoints ────────────────────────────────────────────────────────

@router.post("/documents", status_code=201)
def create_document(payload: DocumentCreate, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    doc_id = f"CDOC-{__import__('uuid').uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO core_documents(id, owner_id, title, source_ref) VALUES (%s, %s, %s, %s) RETURNING *",
                (doc_id, owner_id, payload.title, payload.source_ref),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/documents")
def list_documents(request: Request, lifecycle_state: str | None = None, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if lifecycle_state:
                cur.execute(
                    "SELECT * FROM core_documents WHERE owner_id = %s AND lifecycle_state = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, lifecycle_state, limit))
            else:
                cur.execute(
                    "SELECT * FROM core_documents WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.patch("/documents/{doc_id}/transition")
def transition_document(doc_id: str, payload: DocumentTransition, request: Request) -> dict:
    """Apply a lifecycle state transition — state machine enforced."""
    _db()
    owner_id = owner_for_request(request)
    if not lifecycle_transition_allowed(payload.current_state, payload.target_state):
        raise HTTPException(
            status_code=422,
            detail=f"Transition {payload.current_state} → {payload.target_state} is not allowed",
        )
    applied = apply_document_lifecycle_transition(
        owner_id=owner_id, document_id=doc_id,
        current_state=payload.current_state, target_state=payload.target_state,
    )
    if not applied:
        raise HTTPException(status_code=404, detail="Document not found, not owned by you, or already in target state")
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM core_documents WHERE id = %s AND owner_id = %s", (doc_id, owner_id))
            return cur.fetchone()


@router.post("/documents/{doc_id}/classify", status_code=201)
def classify_document(doc_id: str, payload: DocumentClassify, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM core_documents WHERE id = %s AND owner_id = %s", (doc_id, owner_id))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Document not found")
    cls_id = persist_document_classification(
        owner_id=owner_id, document_id=doc_id,
        document_type=payload.document_type, confidence=payload.confidence,
    )
    if cls_id is None:
        raise HTTPException(status_code=422, detail="Classification could not be stored — validation failed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM core_document_classifications WHERE id = %s AND owner_id = %s", (cls_id, owner_id))
            return cur.fetchone()


# ─── Parallel text endpoints ───────────────────────────────────────────────────

@router.post("/translations", status_code=201)
def create_parallel_text(payload: ParallelTextCreate, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    pt_id = persist_parallel_text(
        owner_id=owner_id,
        source_language=payload.source_language,
        target_language=payload.target_language,
        source=payload.source,
        translation=payload.translation,
        reading=payload.reading,
    )
    if pt_id is None:
        raise HTTPException(status_code=422, detail="Parallel text could not be stored — validation failed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM core_parallel_texts WHERE id = %s AND owner_id = %s", (pt_id, owner_id))
            return cur.fetchone()


@router.get("/translations")
def list_translations(request: Request, source_language: str | None = None, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if source_language:
                cur.execute(
                    "SELECT * FROM core_parallel_texts WHERE owner_id = %s AND source_language = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, source_language, limit))
            else:
                cur.execute(
                    "SELECT * FROM core_parallel_texts WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}
