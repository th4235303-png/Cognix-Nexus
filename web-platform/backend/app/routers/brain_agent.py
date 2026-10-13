from __future__ import annotations
import json
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request
from app.ownership import owner_for_request
from pydantic import BaseModel, Field
from app.services.agent import (
    run_agent_job_now,
    persist_lifecycle_event,
    persist_decision_record,
    build_evidence_refs,
)
from app.store import store

router = APIRouter(prefix="/brain/agent", tags=["brain-agent"])

def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for Agent Mode")
    return store.database

class AgentJobCreate(BaseModel):
    job_type: str = Field(default="knowledge_review", min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(default_factory=list, max_length=30)
    schedule_id: str | None = None
    run_after: datetime | None = None
    expires_at: datetime | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)

class AgentReview(BaseModel):
    status: str = Field(pattern=r"^(accepted|rejected)$")

class DecisionCreate(BaseModel):
    decision: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=4000)
    source_ids: list[str] = Field(default_factory=list, max_length=30,
                                   description="Chunk/source IDs that serve as evidence — required, at least 1")

class DecisionReview(BaseModel):
    review_state: str = Field(pattern=r"^(approved|rejected)$")
    approved_by: str | None = Field(default=None, max_length=200)

@router.post("/jobs", status_code=202)
def create_agent_job(payload: AgentJobCreate, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    job_id = f"AJOB-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO agent_jobs(id,schedule_id,job_type,payload,run_after,expires_at,idempotency_key,owner_id) "
                "VALUES(%s,%s,%s,%s::jsonb,COALESCE(%s,now()),%s,%s,%s) "
                "ON CONFLICT(idempotency_key) DO NOTHING RETURNING *",
                (job_id, payload.schedule_id, payload.job_type,
                 json.dumps({"question": payload.question, "source_ids": payload.source_ids}),
                 payload.run_after, payload.expires_at, payload.idempotency_key, owner_id),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT * FROM agent_jobs WHERE idempotency_key=%s AND owner_id=%s", (payload.idempotency_key, owner_id))
                row = cur.fetchone()
        conn.commit()
    return row

@router.get("/jobs")
def list_agent_jobs(request: Request, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_jobs WHERE owner_id=%s ORDER BY created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}

@router.post("/jobs/{job_id}/execute", status_code=202)
async def execute_agent_job(job_id: str, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM agent_jobs WHERE id=%s AND owner_id=%s", (job_id, owner_id))
            if cur.fetchone() is None: raise HTTPException(status_code=404, detail="Agent job not found")
    ok = await run_agent_job_now(job_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Agent job could not be executed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_jobs WHERE id=%s AND owner_id=%s", (job_id, owner_id))
            return cur.fetchone()

@router.get("/findings")
def list_findings(request: Request, limit: int = 50) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT f.* FROM agent_findings f JOIN agent_jobs j ON j.id=f.job_id WHERE j.owner_id=%s ORDER BY f.created_at DESC LIMIT %s", (owner_id, limit))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}

@router.patch("/findings/{finding_id}/review")
def review_finding(finding_id: str, payload: AgentReview, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE agent_findings SET status=%s,reviewed_at=now() "
                "WHERE id=%s AND status='needs_review' AND job_id IN (SELECT id FROM agent_jobs WHERE owner_id=%s) RETURNING *",
                (payload.status, finding_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Finding not found or already reviewed")
    return row

# ─── Phase 13: Lifecycle Events ───────────────────────────────────────────────

@router.get("/jobs/{job_id}/events")
def list_job_lifecycle_events(job_id: str, request: Request, limit: int = 100) -> dict:
    """Return the durable lifecycle event history for an agent run (append-only log)."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 200))
    with db.connect() as conn:
        with conn.cursor() as cur:
            # Verify ownership before returning events.
            cur.execute("SELECT id FROM agent_jobs WHERE id=%s AND owner_id=%s", (job_id, owner_id))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Agent job not found")
            cur.execute(
                "SELECT * FROM agent_lifecycle_events WHERE job_id=%s "
                "ORDER BY occurred_at ASC LIMIT %s",
                (job_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items), "job_id": job_id}

@router.post("/jobs/{job_id}/events", status_code=201)
def record_lifecycle_event(
    job_id: str,
    request: Request,
    event_type: str = "started",
    idempotency_key: str = "",
) -> dict:
    """Manually record a lifecycle event (e.g. paused, resumed) with terminal fencing."""
    db = _db()
    owner_id = owner_for_request(request)
    if not idempotency_key.strip():
        raise HTTPException(status_code=422, detail="idempotency_key is required")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, status FROM agent_jobs WHERE id=%s AND owner_id=%s", (job_id, owner_id))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Agent job not found")
            run_id = f"ARUN-{uuid4().hex[:8].upper()}"

    inserted = persist_lifecycle_event(
        run_id=run_id,
        job_id=job_id,
        owner_id=owner_id,
        event_type=event_type,
        idempotency_key=idempotency_key,
    )
    return {"inserted": inserted, "idempotency_key": idempotency_key, "job_id": job_id}

# ─── Phase 13: Decision Records ───────────────────────────────────────────────

@router.post("/jobs/{job_id}/decisions", status_code=201)
def create_decision_record(job_id: str, payload: DecisionCreate, request: Request) -> dict:
    """Persist a Phase 13 DecisionRecord — requires at least one evidence source chunk."""
    db = _db()
    owner_id = owner_for_request(request)

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM agent_jobs WHERE id=%s AND owner_id=%s", (job_id, owner_id))
            if cur.fetchone() is None:
                raise HTTPException(status_code=404, detail="Agent job not found")

    if not payload.source_ids:
        raise HTTPException(status_code=422, detail="At least one source_id (evidence) is required for a decision record")

    # Load chunk rows to build typed EvidenceRefs.
    evidence_refs: list[dict] = []
    if payload.source_ids and db.connect:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT c.id, c.content, c.page_number FROM chunks c "
                    "JOIN chapters ch ON ch.id=c.chapter_id "
                    "JOIN books b ON b.id=ch.book_id "
                    "WHERE c.id=ANY(%s) AND b.owner_id=%s ORDER BY c.id",
                    (payload.source_ids, owner_id),
                )
                chunk_rows = cur.fetchall()
        evidence_refs = build_evidence_refs(chunk_rows)

    if not evidence_refs:
        raise HTTPException(status_code=422, detail="No accessible evidence chunks found for the supplied source_ids")

    decision_id = persist_decision_record(
        job_id=job_id,
        owner_id=owner_id,
        decision=payload.decision,
        rationale=payload.rationale,
        evidence_refs=evidence_refs,
    )
    if decision_id is None:
        raise HTTPException(status_code=422, detail="Decision record could not be persisted — validation failed")

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_decisions WHERE id=%s", (decision_id,))
            return cur.fetchone()

@router.get("/decisions")
def list_decisions(request: Request, limit: int = 50) -> dict:
    """List Phase 13 decision records for the authenticated owner."""
    db = _db()
    owner_id = owner_for_request(request)
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM agent_decisions WHERE owner_id=%s "
                "ORDER BY created_at DESC LIMIT %s",
                (owner_id, limit),
            )
            items = cur.fetchall()
    return {"items": items, "total": len(items)}

@router.patch("/decisions/{decision_id}/review")
def review_decision(decision_id: str, payload: DecisionReview, request: Request) -> dict:
    """Approve or reject a Phase 13 decision record.

    No finding becomes canonical without review (Phase 13 invariant 1).
    """
    db = _db()
    owner_id = owner_for_request(request)
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE agent_decisions SET review_state=%s, approved_by=%s, updated_at=now() "
                "WHERE id=%s AND owner_id=%s AND review_state='needs_review' RETURNING *",
                (payload.review_state, payload.approved_by, decision_id, owner_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Decision not found or already reviewed")
    return row
