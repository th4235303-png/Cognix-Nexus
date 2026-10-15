"""Phase 20/21 — Release Evidence and Operational Readiness router.

Phase 20: /release/gates (POST + GET), /release/drills (POST + GET)
Phase 21: /release/checklist (GET evaluate), /release/decisions (POST + GET)

Owner isolation is enforced by RLS — no cross-owner access possible.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import get_current_owner_id
from app.services.release_evidence_service import (
    persist_gate_evidence,
    persist_recovery_drill,
    evaluate_release_checklist,
    persist_release_decision,
)
from app.store import store

router = APIRouter(prefix="/release", tags=["release-evidence"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GateEvidenceIn(BaseModel):
    gate_id: str = Field(..., min_length=1)
    status: str = Field(...)
    evidence_ref: Optional[str] = Field(default=None)
    observed_at: Optional[str] = Field(default=None)


class RecoveryDrillIn(BaseModel):
    drill_id: str = Field(..., min_length=1)
    kind: str = Field(...)
    observed: bool
    recovered: bool
    evidence_ref: Optional[str] = Field(default=None)


class ReleaseDecisionIn(BaseModel):
    revision: str = Field(..., min_length=1, max_length=200)
    approved: bool
    evidence: list[dict] = Field(..., min_length=1)


# ─── Phase 20: Gate Evidence ──────────────────────────────────────────────────

@router.post("/gates", status_code=status.HTTP_201_CREATED)
async def create_gate_evidence(
    body: GateEvidenceIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Persist a Phase 20 gate evidence record."""
    record_id = persist_gate_evidence(
        owner_id=owner_id,
        gate_id=body.gate_id,
        status=body.status,
        evidence_ref=body.evidence_ref,
        observed_at=body.observed_at,
    )
    if record_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gate evidence could not be persisted — validation failed or DB unavailable.",
        )
    return {"id": record_id}


@router.get("/gates")
async def list_gate_evidence(
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 20 gate evidence records for the current owner."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, gate_id, status, evidence_ref, observed_at, created_at "
                "FROM release_gate_evidence WHERE owner_id = %s ORDER BY created_at DESC LIMIT 200",
                (owner_id,),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}


# ─── Phase 20: Recovery Drills ────────────────────────────────────────────────

@router.post("/drills", status_code=status.HTTP_201_CREATED)
async def create_recovery_drill(
    body: RecoveryDrillIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Persist a Phase 20 recovery drill result (fail-closed — must be evidenced)."""
    record_id = persist_recovery_drill(
        owner_id=owner_id,
        drill_id=body.drill_id,
        kind=body.kind,
        observed=body.observed,
        recovered=body.recovered,
        evidence_ref=body.evidence_ref,
    )
    if record_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recovery drill could not be persisted — not evidenced or DB unavailable.",
        )
    return {"id": record_id}


@router.get("/drills")
async def list_recovery_drills(
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 20 recovery drills for the current owner."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, drill_id, kind, observed, recovered, evidence_ref, created_at "
                "FROM release_recovery_drills WHERE owner_id = %s ORDER BY created_at DESC LIMIT 100",
                (owner_id,),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}


# ─── Phase 21: Checklist Evaluation ──────────────────────────────────────────

@router.get("/checklist")
async def get_checklist(
    revision: str = Query(..., min_length=1),
    required_gates: str = Query(..., description="Comma-separated gate IDs"),
    owner_id: str = Depends(get_current_owner_id),
):
    """Phase 21: Evaluate release readiness checklist for the current owner."""
    gates = [g.strip() for g in required_gates.split(",") if g.strip()]
    if not gates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="required_gates must contain at least one gate ID.",
        )
    result = evaluate_release_checklist(
        owner_id=owner_id,
        revision=revision,
        required_gates=gates,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Checklist evaluation failed — DB unavailable or invalid inputs.",
        )
    return result


# ─── Phase 21: Release Decisions ─────────────────────────────────────────────

@router.post("/decisions", status_code=status.HTTP_201_CREATED)
async def create_release_decision(
    body: ReleaseDecisionIn,
    owner_id: str = Depends(get_current_owner_id),
):
    """Phase 21: Persist a release decision with evidence JSONB."""
    record_id = persist_release_decision(
        owner_id=owner_id,
        revision=body.revision,
        approved=body.approved,
        evidence=body.evidence,
    )
    if record_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Release decision could not be persisted — validation failed or DB unavailable.",
        )
    return {"id": record_id}


@router.get("/decisions")
async def list_release_decisions(
    owner_id: str = Depends(get_current_owner_id),
):
    """List Phase 21 release decisions for the current owner."""
    db = store.database
    if db is None:
        return {"items": []}
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, revision, approved, evidence, created_at "
                "FROM release_decisions WHERE owner_id = %s ORDER BY created_at DESC LIMIT 100",
                (owner_id,),
            )
            rows = cur.fetchall() or []
    return {"items": [dict(r) for r in rows]}
