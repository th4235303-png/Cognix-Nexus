from __future__ import annotations

"""Phase 16 — Advanced Layer API router.

Endpoints:
  POST  /advanced/wiki                     Create a wiki entity (source lineage required)
  GET   /advanced/wiki                     List wiki entities
  PATCH /advanced/wiki/{id}/review         Review a wiki entity
  POST  /advanced/metrics                  Record a growth metric (evidence+derivation required)
  GET   /advanced/metrics                  List growth metrics
  POST  /advanced/handoffs                 Register an offline handoff ref
  GET   /advanced/handoffs                 List handoff refs
  POST  /advanced/secrets                  Register a secret ref (ciphertext_ref only)
  GET   /advanced/secrets                  List secret refs

Phase 16 invariants preserved:
  1. WikiEntity requires source_refs (lineage required).
  2. GrowthMetric requires evidence_refs + derivation (explainability required).
  3. OfflineHandoff stores artifact_ref only — no payload through this API.
  4. SecretRef stores ciphertext_ref only — raw secrets never accepted.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.ownership import owner_for_request
from app.store import store
from app.services.advanced_layer_service import (
    persist_wiki_entity,
    persist_growth_metric,
    persist_offline_handoff,
    persist_secret_ref,
)

router = APIRouter(prefix="/advanced", tags=["advanced-layer"])

_ENTITY_TYPES = {"person","organization","place","concept","technology","event","product","book","term","other"}
_HANDOFF_FORMATS = {"encrypted_archive", "signed_manifest"}
_SECRET_KINDS = {"totp", "ssh_key", "credential"}


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for Advanced Layer")
    return store.database


# ─── Pydantic models ──────────────────────────────────────────────────────────

class WikiEntityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    entity_type: str = Field(pattern=r"^(person|organization|place|concept|technology|event|product|book|term|other)$")
    source_refs: list[str] = Field(min_length=1, max_length=20, description="Source IDs for lineage — required")

    @field_validator("source_refs")
    @classmethod
    def source_refs_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("source_refs must have at least one entry (lineage required)")
        return v


class WikiEntityReview(BaseModel):
    review_state: str = Field(pattern=r"^(needs_review|approved|rejected)$")


class GrowthMetricCreate(BaseModel):
    metric: str = Field(min_length=1, max_length=200)
    value: float
    unit: str = Field(min_length=1, max_length=50)
    evidence_refs: list[str] = Field(min_length=1, max_length=20, description="Evidence IDs — required")
    derivation: str = Field(min_length=1, max_length=2000, description="Derivation explanation — required")

    @field_validator("evidence_refs")
    @classmethod
    def evidence_refs_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("evidence_refs must have at least one entry")
        return v


class HandoffCreate(BaseModel):
    format: str = Field(pattern=r"^(encrypted_archive|signed_manifest)$")
    artifact_ref: str = Field(min_length=1, max_length=2000, description="URI to artifact — not the payload")
    recoverable: bool = True


class SecretRefCreate(BaseModel):
    kind: str = Field(pattern=r"^(totp|ssh_key|credential)$")
    ciphertext_ref: str = Field(min_length=1, max_length=2000, description="URI to ciphertext storage — not the secret")


# ─── Wiki endpoints ────────────────────────────────────────────────────────────

@router.post("/wiki", status_code=201)
def create_wiki_entity(payload: WikiEntityCreate, request: Request) -> dict:
    """Create a wiki entity — source lineage refs required."""
    db = _db()
    owner_id = owner_for_request(request)

    entity_id = persist_wiki_entity(
        owner_id=owner_id,
        name=payload.name,
        entity_type=payload.entity_type,
        source_refs=payload.source_refs,
    )
    if entity_id is None:
        raise HTTPException(status_code=422, detail="Wiki entity could not be created — validation failed")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM advanced_wiki_entities WHERE id = %s AND owner_id = %s", (entity_id, owner_id))
            return cur.fetchone()


@router.get("/wiki")
def list_wiki_entities(request: Request, entity_type: str | None = None, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if entity_type:
                cur.execute(
                    "SELECT * FROM advanced_wiki_entities WHERE owner_id = %s AND entity_type = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, entity_type, limit))
            else:
                cur.execute(
                    "SELECT * FROM advanced_wiki_entities WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.patch("/wiki/{entity_id}/review")
def review_wiki_entity(entity_id: str, payload: WikiEntityReview, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE advanced_wiki_entities SET review_state = %s, updated_at = now() "
                "WHERE id = %s AND owner_id = %s AND review_state = 'draft' RETURNING *",
                (payload.review_state, entity_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Wiki entity not found or already reviewed")
    return row


# ─── Growth metric endpoints ───────────────────────────────────────────────────

@router.post("/metrics", status_code=201)
def record_growth_metric(payload: GrowthMetricCreate, request: Request) -> dict:
    """Record a growth metric — evidence and derivation both required."""
    db = _db()
    owner_id = owner_for_request(request)

    metric_id = persist_growth_metric(
        owner_id=owner_id,
        metric=payload.metric,
        value=payload.value,
        unit=payload.unit,
        evidence_refs=payload.evidence_refs,
        derivation=payload.derivation,
    )
    if metric_id is None:
        raise HTTPException(status_code=422, detail="Growth metric could not be recorded — validation failed")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM advanced_growth_metrics WHERE id = %s AND owner_id = %s", (metric_id, owner_id))
            return cur.fetchone()


@router.get("/metrics")
def list_growth_metrics(request: Request, metric: str | None = None, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if metric:
                cur.execute(
                    "SELECT * FROM advanced_growth_metrics WHERE owner_id = %s AND metric = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, metric, limit))
            else:
                cur.execute(
                    "SELECT * FROM advanced_growth_metrics WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


# ─── Offline handoff endpoints ─────────────────────────────────────────────────

@router.post("/handoffs", status_code=201)
def register_handoff(payload: HandoffCreate, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    handoff_id = persist_offline_handoff(
        owner_id=owner_id, format=payload.format,
        artifact_ref=payload.artifact_ref, recoverable=payload.recoverable,
    )
    if handoff_id is None:
        raise HTTPException(status_code=422, detail="Handoff ref could not be registered — validation failed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM advanced_offline_handoffs WHERE id = %s AND owner_id = %s", (handoff_id, owner_id))
            return cur.fetchone()


@router.get("/handoffs")
def list_handoffs(request: Request, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM advanced_offline_handoffs WHERE owner_id = %s ORDER BY created_at DESC LIMIT %s",
                (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


# ─── Secret ref endpoints ──────────────────────────────────────────────────────

@router.post("/secrets", status_code=201)
def register_secret_ref(payload: SecretRefCreate, request: Request) -> dict:
    """Register a secret ref — ciphertext_ref URI only, never the raw secret."""
    db = _db()
    owner_id = owner_for_request(request)
    secret_id = persist_secret_ref(
        owner_id=owner_id, kind=payload.kind, ciphertext_ref=payload.ciphertext_ref,
    )
    if secret_id is None:
        raise HTTPException(status_code=422, detail="Secret ref could not be registered — validation failed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM advanced_secret_refs WHERE id = %s AND owner_id = %s", (secret_id, owner_id))
            return cur.fetchone()


@router.get("/secrets")
def list_secret_refs(request: Request, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM advanced_secret_refs WHERE owner_id = %s ORDER BY created_at DESC LIMIT %s",
                (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}
