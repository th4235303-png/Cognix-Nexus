from __future__ import annotations

"""Phase 14 — Learning Science API router.

Endpoints:
  POST   /learning/signals            Record a learning signal (evidence-required)
  GET    /learning/signals             List owner's signals (recent-first)
  GET    /learning/path                Compute a decay-ranked learning path from DB signals
  POST   /learning/path                Persist a learning path (evidence-required per item)
  PATCH  /learning/path/{item_id}/review  Activate / complete / skip a path item

All routes require a valid JWT (owner_id extracted via owner_for_request).
All routes fail with 503 if store.database is None (in-memory mode).

Phase 14 invariants preserved:
  1. No path item becomes active without an explicit reason.
  2. Evidence refs must be attached to every persisted signal.
  3. decay_weight() is deterministic — no override at runtime.
  4. Signals are append-only; no UPDATE of existing signals.
"""

import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.ownership import owner_for_request
from app.store import store
from app.services.learning_science_service import (
    persist_learning_signal,
    persist_learning_path,
    build_path_from_db,
)
from app.services.learning_science import LearningPathItem

router = APIRouter(prefix="/learning", tags=["learning"])

_SIGNAL_TYPES = {"review", "recall", "completion", "difficulty", "reflection"}
_REVIEW_STATES = {"active", "completed", "skipped"}


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for Learning Science")
    return store.database


# ─── Pydantic models ─────────────────────────────────────────────────────────

class SignalCreate(BaseModel):
    subject_id: str = Field(min_length=1, max_length=200)
    signal_type: str = Field(pattern=r"^(review|recall|completion|difficulty|reflection)$")
    strength: float = Field(ge=0.0, le=1.0)
    source_ids: list[str] = Field(
        default_factory=list,
        description="Chunk/source IDs that serve as evidence — at least 1 required",
    )
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator("source_ids")
    @classmethod
    def source_ids_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("source_ids must have at least one entry (evidence required)")
        return v


class PathItemCreate(BaseModel):
    subject_id: str = Field(min_length=1, max_length=200)
    position: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=2000)
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence ref IDs — at least 1 required",
    )

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("evidence_refs must have at least one entry (evidence required)")
        return v


class PathCreate(BaseModel):
    items: list[PathItemCreate] = Field(min_length=1, max_length=50)


class PathItemReview(BaseModel):
    review_state: str = Field(pattern=r"^(active|completed|skipped)$")


# ─── Signal endpoints ─────────────────────────────────────────────────────────

@router.post("/signals", status_code=201)
def record_signal(payload: SignalCreate, request: Request) -> dict:
    """Record a Phase 14 LearningSignal — evidence (source_ids) required."""
    db = _db()
    owner_id = owner_for_request(request)

    # Build evidence_refs from source_ids (stored as-is; no DB chunk lookup
    # required for signals — subject_id is the primary key for learning state).
    evidence_refs = [{"source_type": "source", "source_id": sid} for sid in payload.source_ids[:30]]

    signal_id = persist_learning_signal(
        owner_id=owner_id,
        subject_id=payload.subject_id,
        signal_type=payload.signal_type,
        strength=payload.strength,
        evidence_refs=evidence_refs,
        idempotency_key=payload.idempotency_key,
    )
    if signal_id is None:
        raise HTTPException(status_code=422, detail="Signal could not be persisted — validation failed")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM learning_signals WHERE id = %s AND owner_id = %s",
                (signal_id, owner_id),
            )
            return cur.fetchone()


@router.get("/signals")
def list_signals(request: Request, limit: int = 50) -> dict:
    """List recent learning signals for the authenticated owner."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM learning_signals WHERE owner_id = %s "
                "ORDER BY occurred_at DESC LIMIT %s",
                (owner_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


# ─── Learning path endpoints ───────────────────────────────────────────────────

@router.get("/path")
def get_learning_path(
    request: Request,
    half_life_days: float = 14.0,
    limit: int = 10,
) -> dict:
    """Compute a decay-ranked learning path from the owner's recent signals.

    Uses deterministic decay_weight(age_days, half_life_days) × weakness.
    No LLM involved. No side effects — read-only.
    """
    _db()
    owner_id = owner_for_request(request)
    half_life_days = max(1.0, min(half_life_days, 365.0))
    limit = max(1, min(limit, 50))

    path = build_path_from_db(owner_id, half_life_days=half_life_days, limit=limit)
    return {
        "items": [
            {
                "subject_id": item.subject_id,
                "position": item.position,
                "reason": item.reason,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in path
        ],
        "total": len(path),
        "half_life_days": half_life_days,
    }


@router.post("/path", status_code=201)
def persist_path(payload: PathCreate, request: Request) -> dict:
    """Persist a learning path — each item must carry evidence refs and a reason."""
    _db()
    owner_id = owner_for_request(request)

    items = [
        LearningPathItem(
            id=f"LPATH-{i}",
            subject_id=item.subject_id,
            position=item.position,
            reason=item.reason,
            evidence_refs=tuple(item.evidence_refs),
        )
        for i, item in enumerate(payload.items)
    ]

    inserted_ids = persist_learning_path(owner_id=owner_id, items=items)
    if not inserted_ids:
        raise HTTPException(
            status_code=422,
            detail="No path items could be persisted — each item requires a reason and at least one evidence ref",
        )
    return {"inserted_ids": inserted_ids, "total": len(inserted_ids)}


@router.get("/path/items")
def list_path_items(request: Request, limit: int = 50) -> dict:
    """List persisted learning path items for the authenticated owner."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM learning_path_items WHERE owner_id = %s "
                "ORDER BY position ASC, created_at DESC LIMIT %s",
                (owner_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.patch("/path/{item_id}/review")
def review_path_item(item_id: str, payload: PathItemReview, request: Request) -> dict:
    """Activate, complete, or skip a learning path item.

    Phase 14 invariant: only 'draft' items can transition via this endpoint.
    """
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE learning_path_items SET review_state = %s, updated_at = now() "
                "WHERE id = %s AND owner_id = %s AND review_state = 'draft' RETURNING *",
                (payload.review_state, item_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Path item not found, not owned by you, or already reviewed",
        )
    return row
