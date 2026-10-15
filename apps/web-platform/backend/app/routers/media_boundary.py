"""Phase 18/19 — Media Boundary and Native Capabilities router.

Phase 18: /media/assets (POST + GET list), /media/assets/{id}/ocr (POST + GET list)
Phase 19: /media/device-gates (POST + GET list)

Owner isolation is enforced by RLS — no cross-owner access possible.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import get_current_owner_id
from app.services.media_boundary_service import (
    persist_media_asset,
    persist_ocr_result,
    persist_device_gate,
)
from app.store import store

router = APIRouter(prefix="/media", tags=["media-boundary"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class MediaAssetIn(BaseModel):
    storage_ref: str = Field(..., min_length=1, max_length=2000)
    content_sha256: str = Field(..., min_length=1, max_length=64)
    source_ref: str = Field(..., min_length=1, max_length=2000)


class OCRResultIn(BaseModel):
    text: str = Field(default="")
    source_ref: str = Field(..., min_length=1, max_length=2000)
    provider: str = Field(..., min_length=1, max_length=200)
    status: str = Field(default="draft")


class DeviceGateIn(BaseModel):
    capability: str = Field(..., min_length=1)
    device_verified: bool
    user_enabled: bool


# ─── Phase 18: Media Assets ───────────────────────────────────────────────────

@router.post("/assets", status_code=status.HTTP_201_CREATED)
async def create_media_asset(
    body: MediaAssetIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Register a Phase 18 media asset (storage reference only — no raw bytes)."""
    asset_id = persist_media_asset(
        owner_id=owner_id,
        storage_ref=body.storage_ref,
        content_sha256=body.content_sha256,
        source_ref=body.source_ref,
    )
    if asset_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Media asset could not be persisted — validation failed or DB unavailable.",
        )
    return {"id": asset_id}


@router.get("/assets")
async def list_media_assets(
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 18 media assets for the current owner."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, storage_ref, content_sha256, source_ref, created_at "
                "FROM media_assets WHERE owner_id = %s ORDER BY created_at DESC LIMIT 200",
                (owner_id,),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}


# ─── Phase 18: OCR Results ────────────────────────────────────────────────────

@router.post("/assets/{asset_id}/ocr", status_code=status.HTTP_201_CREATED)
async def create_ocr_result(
    asset_id: str,
    body: OCRResultIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Persist a Phase 18 OCR result linked to a media asset."""
    ocr_id = persist_ocr_result(
        owner_id=owner_id,
        asset_id=asset_id,
        text=body.text,
        source_ref=body.source_ref,
        provider=body.provider,
        status=body.status,
    )
    if ocr_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="OCR result could not be persisted — lineage validation failed or DB unavailable.",
        )
    return {"id": ocr_id}


@router.get("/assets/{asset_id}/ocr")
async def list_ocr_results(
    asset_id: str,
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 18 OCR results for a media asset."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, asset_id, text, source_ref, provider, status, created_at "
                "FROM media_ocr_results "
                "WHERE owner_id = %s AND asset_id = %s "
                "ORDER BY created_at DESC LIMIT 100",
                (owner_id, asset_id),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}


# ─── Phase 19: Device Gates ───────────────────────────────────────────────────

@router.post("/device-gates", status_code=status.HTTP_201_CREATED)
async def create_device_gate(
    body: DeviceGateIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Persist a Phase 19 device capability gate (only when activatable)."""
    gate_id = persist_device_gate(
        owner_id=owner_id,
        capability=body.capability,
        device_verified=body.device_verified,
        user_enabled=body.user_enabled,
    )
    if gate_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Device gate could not be persisted — capability not activatable or DB unavailable.",
        )
    return {"id": gate_id}


@router.get("/device-gates")
async def list_device_gates(
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 19 device capability gates for the current owner."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, capability, device_verified, user_enabled, created_at "
                "FROM media_device_gates WHERE owner_id = %s ORDER BY created_at DESC LIMIT 100",
                (owner_id,),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}
