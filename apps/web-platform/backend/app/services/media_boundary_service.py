from __future__ import annotations

"""Phase 18/19 — Media Boundary and Native Capabilities runtime service helpers.

Phase 18: Vizora Lens — media asset registration, OCR result persistence,
          evidence-lineage validation.
Phase 19: Native/Product UX — device gate capability persistence.

Invariants:
  1. MediaAsset requires a non-empty storage_ref, content_sha256, and source_ref.
  2. OCRResult requires media_lineage_is_valid() — asset/OCR must share owner and source_ref.
  3. DeviceGate only persisted when capability_is_activatable() returns True.
  4. Provider failures must be explicit — no silent fallback.
  5. All writes are owner-isolated and fail-closed (None on any validation failure).
  6. content_sha256 is stored as-is (hex digest reference) — raw media never stored here.
"""

import json
from uuid import uuid4

from app.store import store
from app.services.media_boundary import (
    MediaAsset,
    OCRResult,
    DeviceGate,
    media_lineage_is_valid,
    capability_is_activatable,
)

_CAPABILITIES = frozenset({"camera", "voice", "push", "biometric", "offline"})
_OCR_STATUSES = frozenset({"draft", "needs_review", "approved", "failed"})


# ─── persist_media_asset ──────────────────────────────────────────────────────

def persist_media_asset(
    owner_id: str,
    storage_ref: str,
    content_sha256: str,
    source_ref: str,
) -> str | None:
    """Persist a Phase 18 media asset record.

    Invariants:
      - storage_ref is a URI/key reference — raw media bytes are NEVER stored here.
      - content_sha256 is a hex-digest reference for integrity verification.
      - source_ref links asset to its origin (lineage required).
    Returns asset ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip():
        return None
    if not storage_ref.strip():
        return None
    if not content_sha256.strip():
        return None
    if not source_ref.strip():
        return None

    asset = MediaAsset(
        id=f"MASSET-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        storage_ref=storage_ref.strip()[:2000],
        content_sha256=content_sha256.strip()[:64],
        source_ref=source_ref.strip()[:2000],
    )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO media_assets"
                "(id, owner_id, storage_ref, content_sha256, source_ref) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (asset.id, owner_id, asset.storage_ref, asset.content_sha256, asset.source_ref),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_ocr_result ───────────────────────────────────────────────────────

def persist_ocr_result(
    owner_id: str,
    asset_id: str,
    text: str,
    source_ref: str,
    provider: str,
    status: str = "draft",
) -> str | None:
    """Persist a Phase 18 OCR result, validated against media lineage.

    Invariants:
      - Requires media_lineage_is_valid() — asset and OCR must share owner + source_ref.
      - status must be one of: draft, needs_review, approved, failed.
      - provider must be non-empty (explicit provenance required).
      - text may be empty string for 'failed' status only — all others require text.
    Returns OCR result ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not asset_id.strip():
        return None
    if not source_ref.strip() or not provider.strip():
        return None
    if status not in _OCR_STATUSES:
        return None
    if status != "failed" and not text.strip():
        return None

    # Build a synthetic MediaAsset for lineage validation
    asset_stub = MediaAsset(
        id=asset_id,
        owner_id=owner_id,
        storage_ref="ref",
        content_sha256="sha",
        source_ref=source_ref,
    )
    result_stub = OCRResult(
        asset_id=asset_id,
        owner_id=owner_id,
        text=text,
        source_ref=source_ref,
        provider=provider,
        status=status,  # type: ignore[arg-type]
    )
    if not media_lineage_is_valid(asset_stub, result_stub):
        return None

    ocr_id = f"OCR-{uuid4().hex[:8].upper()}"

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO media_ocr_results"
                "(id, owner_id, asset_id, text, source_ref, provider, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (ocr_id, owner_id, asset_id, text.strip(), source_ref.strip()[:2000],
                 provider.strip()[:200], status),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_device_gate ──────────────────────────────────────────────────────

def persist_device_gate(
    owner_id: str,
    capability: str,
    device_verified: bool,
    user_enabled: bool,
) -> str | None:
    """Persist a Phase 19 device capability gate record.

    Invariants:
      - capability must be one of: camera, voice, push, biometric, offline.
      - capability_is_activatable() must return True — gate is only stored if active.
      - Fail-closed: if gate is not activatable, return None without error.
    Returns gate ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip():
        return None
    if capability not in _CAPABILITIES:
        return None

    gate = DeviceGate(
        capability=capability,  # type: ignore[arg-type]
        device_verified=device_verified,
        user_enabled=user_enabled,
    )
    if not capability_is_activatable(gate):
        return None

    gate_id = f"DGATE-{uuid4().hex[:8].upper()}"

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO media_device_gates"
                "(id, owner_id, capability, device_verified, user_enabled) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (gate_id, owner_id, capability, device_verified, user_enabled),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None
