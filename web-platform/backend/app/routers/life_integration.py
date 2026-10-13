from __future__ import annotations

"""Phase 15 — Life Integration API router.

Endpoints:
  POST   /life/restore                  Submit explicit context restore request
  GET    /life/restore                  List owner's restore requests
  PATCH  /life/restore/{id}/status      Update restore request status (applied/denied/expired)
  POST   /life/consent                  Record consent grant or revocation (append-only)
  GET    /life/consent                  List consent events (most-recent-first per scope)
  POST   /life/capsules                 Register an encrypted capsule ref (metadata only)
  GET    /life/capsules                 List capsule refs for owner

Phase 15 invariants preserved:
  1. Context restore is ONLY triggered by explicit user request.
  2. Cross-feature restore is never implicit — always fails closed.
  3. Consent events are append-only; revocation adds a new event, never deletes.
  4. Capsule refs store metadata only — ciphertext never passes through this API.
  5. Owner mismatch always fails closed.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.ownership import owner_for_request
from app.store import store
from app.services.life_integration_service import (
    persist_restore_request,
    persist_consent_event,
    persist_capsule_ref,
)

router = APIRouter(prefix="/life", tags=["life-integration"])

_KNOWN_ALGORITHMS = {"AES-256-GCM", "ChaCha20-Poly1305"}


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for Life Integration")
    return store.database


# ─── Pydantic models ──────────────────────────────────────────────────────────

class RestoreCreate(BaseModel):
    scope: list[str] = Field(min_length=1, max_length=20, description="Feature scopes to restore")
    reason: str = Field(min_length=1, max_length=2000)
    idempotency_key: str = Field(min_length=1, max_length=200)

    @field_validator("scope")
    @classmethod
    def scope_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("scope must have at least one entry")
        return [s.strip() for s in v if s.strip()]


class RestoreStatusUpdate(BaseModel):
    status: str = Field(pattern=r"^(applied|denied|expired)$")


class ConsentCreate(BaseModel):
    feature_scope: str = Field(min_length=1, max_length=200)
    action: str = Field(pattern=r"^(granted|revoked)$")
    idempotency_key: str = Field(min_length=1, max_length=200)


class CapsuleCreate(BaseModel):
    ciphertext_ref: str = Field(
        min_length=1, max_length=2000,
        description="URI or key reference to external ciphertext storage — NOT the ciphertext itself",
    )
    algorithm: str = Field(pattern=r"^(AES-256-GCM|ChaCha20-Poly1305)$")
    exportable: bool = True


# ─── Restore endpoints ────────────────────────────────────────────────────────

@router.post("/restore", status_code=201)
def submit_restore_request(payload: RestoreCreate, request: Request) -> dict:
    """Submit an explicit user-triggered context restore request.

    Fails with 422 if can_restore() fails (owner, scope, or user-trigger missing).
    """
    db = _db()
    owner_id = owner_for_request(request)

    restore_id = persist_restore_request(
        owner_id=owner_id,
        scope=payload.scope,
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    if restore_id is None:
        raise HTTPException(
            status_code=422,
            detail="Restore request could not be created — must be user-triggered with a valid scope and reason",
        )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM life_restore_requests WHERE id = %s AND owner_id = %s",
                (restore_id, owner_id),
            )
            return cur.fetchone()


@router.get("/restore")
def list_restore_requests(request: Request, limit: int = 50) -> dict:
    """List the authenticated owner's restore requests (most recent first)."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM life_restore_requests WHERE owner_id = %s "
                "ORDER BY created_at DESC LIMIT %s",
                (owner_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.patch("/restore/{restore_id}/status")
def update_restore_status(restore_id: str, payload: RestoreStatusUpdate, request: Request) -> dict:
    """Update a restore request status (applied/denied/expired).

    Only 'pending' requests can be transitioned.
    """
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE life_restore_requests SET status = %s, updated_at = now() "
                "WHERE id = %s AND owner_id = %s AND status = 'pending' RETURNING *",
                (payload.status, restore_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Restore request not found, not owned by you, or already resolved",
        )
    return row


# ─── Consent endpoints ────────────────────────────────────────────────────────

@router.post("/consent", status_code=201)
def record_consent(payload: ConsentCreate, request: Request) -> dict:
    """Record a consent grant or revocation (append-only — never deletes or overwrites)."""
    db = _db()
    owner_id = owner_for_request(request)

    event_id = persist_consent_event(
        owner_id=owner_id,
        feature_scope=payload.feature_scope,
        action=payload.action,
        idempotency_key=payload.idempotency_key,
    )
    if event_id is None:
        raise HTTPException(
            status_code=422,
            detail="Consent event could not be persisted — validation failed",
        )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM life_consent_events WHERE id = %s AND owner_id = %s",
                (event_id, owner_id),
            )
            return cur.fetchone()


@router.get("/consent")
def list_consent_events(request: Request, feature_scope: str | None = None, limit: int = 50) -> dict:
    """List consent events for the owner, optionally filtered by feature_scope."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            if feature_scope:
                cur.execute(
                    "SELECT * FROM life_consent_events WHERE owner_id = %s AND feature_scope = %s "
                    "ORDER BY created_at DESC LIMIT %s",
                    (owner_id, feature_scope, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM life_consent_events WHERE owner_id = %s "
                    "ORDER BY created_at DESC LIMIT %s",
                    (owner_id, limit),
                )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


# ─── Capsule ref endpoints ────────────────────────────────────────────────────

@router.post("/capsules", status_code=201)
def register_capsule(payload: CapsuleCreate, request: Request) -> dict:
    """Register an encrypted capsule reference (metadata only — no ciphertext stored)."""
    db = _db()
    owner_id = owner_for_request(request)

    capsule_id = persist_capsule_ref(
        owner_id=owner_id,
        ciphertext_ref=payload.ciphertext_ref,
        algorithm=payload.algorithm,
        exportable=payload.exportable,
    )
    if capsule_id is None:
        raise HTTPException(
            status_code=422,
            detail="Capsule ref could not be persisted — validation failed",
        )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM life_capsule_refs WHERE id = %s AND owner_id = %s",
                (capsule_id, owner_id),
            )
            return cur.fetchone()


@router.get("/capsules")
def list_capsules(request: Request, limit: int = 50) -> dict:
    """List encrypted capsule refs for the authenticated owner."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM life_capsule_refs WHERE owner_id = %s "
                "ORDER BY created_at DESC LIMIT %s",
                (owner_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}
