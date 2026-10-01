from __future__ import annotations

from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.store import store

router = APIRouter(prefix="/brain/intelligence", tags=["intelligence"])


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for this feature")
    return store.database


class ReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    question: str = Field(min_length=1, max_length=4000)
    methodology: dict = Field(default_factory=dict)


@router.post("/research/reports", status_code=201)
def create_report(payload: ReportCreate) -> dict:
    db = _db()
    report_id = f"RPT-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO research_reports(id,title,question,methodology) VALUES(%s,%s,%s,%s) RETURNING *",
                (report_id, payload.title, payload.question, payload.methodology),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/research/reports")
def list_reports() -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM research_reports ORDER BY updated_at DESC LIMIT 100")
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


class ClaimCreate(BaseModel):
    claim: str = Field(min_length=1, max_length=4000)
    source_ids: list[str] = Field(default_factory=list, max_length=50)
    verification_state: str = Field(default="unverified", pattern=r"^(unverified|supported|contradicted|needs_review)$")
    confidence: str = Field(default="low", pattern=r"^(low|medium|high)$")
    notes: str | None = None


@router.post("/research/reports/{report_id}/claims", status_code=201)
def add_claim(report_id: str, payload: ClaimCreate) -> dict:
    db = _db()
    claim_id = f"CLM-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM research_reports WHERE id=%s", (report_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Research report not found")
            cur.execute(
                "INSERT INTO research_claims(id,report_id,claim,source_ids,verification_state,confidence,notes) VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s) RETURNING *",
                (claim_id, report_id, payload.claim, json.dumps(payload.source_ids), payload.verification_state, payload.confidence, payload.notes),
            )
            row = cur.fetchone()
        conn.commit()
    return row


class ReviewCreate(BaseModel):
    decision: str = Field(pattern=r"^(approve|reject|needs_revision)$")
    notes: str | None = None


@router.post("/research/reports/{report_id}/review", status_code=201)
def review_report(report_id: str, payload: ReviewCreate) -> dict:
    db = _db()
    review_id = f"RREV-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM research_reports WHERE id=%s", (report_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Research report not found")
            cur.execute(
                "INSERT INTO research_reviews(id,report_id,decision,notes) VALUES(%s,%s,%s,%s) RETURNING *",
                (review_id, report_id, payload.decision, payload.notes),
            )
            row = cur.fetchone()
            cur.execute("UPDATE research_reports SET status=%s,updated_at=now() WHERE id=%s", (payload.decision, report_id))
        conn.commit()
    return row


class MediaAnalysisCreate(BaseModel):
    result: dict
    model: str | None = None
    prompt_version: str | None = None
    copyright_status: str = Field(default="unknown", pattern=r"^(unknown|user_owned|licensed|public_domain|restricted)$")


@router.post("/media/{media_id}/analysis", status_code=201)
def save_media_analysis(media_id: str, payload: MediaAnalysisCreate) -> dict:
    db = _db()
    analysis_id = f"MAN-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM media_assets WHERE id=%s", (media_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Media asset not found")
            cur.execute(
                "INSERT INTO media_analysis(id,media_id,model,prompt_version,result,copyright_status) VALUES(%s,%s,%s,%s,%s::jsonb,%s) RETURNING *",
                (analysis_id, media_id, payload.model, payload.prompt_version, json.dumps(payload.result), payload.copyright_status),
            )
            row = cur.fetchone()
        conn.commit()
    return row


class PathCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    goal: str = Field(min_length=1, max_length=2000)
    items: list[dict] = Field(default_factory=list, max_length=100)


@router.post("/learning/paths", status_code=201)
def create_learning_path(payload: PathCreate) -> dict:
    db = _db()
    path_id = f"PATH-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO learning_paths(id,title,goal,items) VALUES(%s,%s,%s,%s::jsonb) RETURNING *",
                (path_id, payload.title, payload.goal, json.dumps(payload.items)),
            )
            row = cur.fetchone()
        conn.commit()
    return row


class GapCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    evidence: list[dict] = Field(default_factory=list, max_length=100)


@router.post("/learning/gaps", status_code=201)
def create_gap(payload: GapCreate) -> dict:
    db = _db()
    gap_id = f"GAP-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO knowledge_gaps(id,subject,evidence) VALUES(%s,%s,%s::jsonb) RETURNING *",
                (gap_id, payload.subject, json.dumps(payload.evidence)),
            )
            row = cur.fetchone()
        conn.commit()
    return row


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    question: str = Field(min_length=1, max_length=3000)
    options: list[dict] = Field(default_factory=list, max_length=20)
    evidence: list[dict] = Field(default_factory=list, max_length=100)


@router.post("/decisions", status_code=201)
def create_decision(payload: DecisionCreate) -> dict:
    db = _db()
    decision_id = f"DEC-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO decisions(id,title,question,options,evidence) VALUES(%s,%s,%s,%s::jsonb,%s::jsonb) RETURNING *",
                (decision_id, payload.title, payload.question, json.dumps(payload.options), json.dumps(payload.evidence)),
            )
            row = cur.fetchone()
        conn.commit()
    return row


class WritingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body: str = ""
    source_ids: list[str] = Field(default_factory=list, max_length=100)


@router.post("/writing", status_code=201)
def create_writing(payload: WritingCreate) -> dict:
    db = _db()
    writing_id = f"WRITE-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO writing_drafts(id,title,body,source_ids) VALUES(%s,%s,%s,%s::jsonb) RETURNING *",
                (writing_id, payload.title, payload.body, json.dumps(payload.source_ids)),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/offline/policy")
def offline_policy() -> dict:
    return {
        "capture": "local_first",
        "cache": "encrypted_local",
        "cloud_processing": "explicit_user_permission",
        "full_on_device_ai": False,
        "sync": "revisioned",
    }


class CapsuleCreate(BaseModel):
    label: str = Field(min_length=1, max_length=300)
    ciphertext: str = Field(min_length=1)
    nonce: str = Field(min_length=1)
    kdf_salt: str = Field(min_length=1)
    kdf_params: dict = Field(default_factory=dict)
    beneficiary_hint: str | None = Field(default=None, max_length=300)


@router.post("/life/capsules", status_code=201)
def create_capsule(payload: CapsuleCreate) -> dict:
    db = _db()
    capsule_id = f"CAP-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO encrypted_capsules(id,label,ciphertext,nonce,kdf_salt,kdf_params,beneficiary_hint) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id,label,nonce,kdf_salt,kdf_params,beneficiary_hint,created_at",
                (capsule_id, payload.label, payload.ciphertext, payload.nonce, payload.kdf_salt, payload.kdf_params, payload.beneficiary_hint),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/life/mood-policy")
def mood_policy() -> dict:
    return {
        "storage": "local_only",
        "server_logging": False,
        "cloud_sync": "disabled_by_default",
        "purpose": "user_controlled_context_only",
    }
