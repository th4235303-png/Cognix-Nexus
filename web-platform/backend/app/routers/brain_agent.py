from __future__ import annotations
import json
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.agent import run_agent_job_now
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

@router.post("/jobs", status_code=202)
def create_agent_job(payload: AgentJobCreate) -> dict:
    db = _db()
    job_id = f"AJOB-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO agent_jobs(id,schedule_id,job_type,payload,run_after,expires_at,idempotency_key) "
                "VALUES(%s,%s,%s,%s::jsonb,COALESCE(%s,now()),%s,%s) "
                "ON CONFLICT(idempotency_key) DO NOTHING RETURNING *",
                (job_id, payload.schedule_id, payload.job_type,
                 json.dumps({"question": payload.question, "source_ids": payload.source_ids}),
                 payload.run_after, payload.expires_at, payload.idempotency_key),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT * FROM agent_jobs WHERE idempotency_key=%s", (payload.idempotency_key,))
                row = cur.fetchone()
        conn.commit()
    return row

@router.get("/jobs")
def list_agent_jobs(limit: int = 50) -> dict:
    db = _db()
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_jobs ORDER BY created_at DESC LIMIT %s", (limit,))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}

@router.post("/jobs/{job_id}/execute", status_code=202)
async def execute_agent_job(job_id: str) -> dict:
    db = _db()
    ok = await run_agent_job_now(job_id)
    if not ok:
        raise HTTPException(status_code=409, detail="Agent job could not be executed")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_jobs WHERE id=%s", (job_id,))
            return cur.fetchone()

@router.get("/findings")
def list_findings(limit: int = 50) -> dict:
    db = _db()
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agent_findings ORDER BY created_at DESC LIMIT %s", (limit,))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}

@router.patch("/findings/{finding_id}/review")
def review_finding(finding_id: str, payload: AgentReview) -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE agent_findings SET status=%s,reviewed_at=now() "
                "WHERE id=%s AND status='needs_review' RETURNING *",
                (payload.status, finding_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Finding not found or already reviewed")
    return row
