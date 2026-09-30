from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.services.trust import calculate_trust
from app.store import now_iso, store

router = APIRouter()


class SourceCreate(BaseModel):
    url: HttpUrl
    note: str | None = None


class ClaimCreate(BaseModel):
    text: str = Field(min_length=1)
    excerpt: str | None = None
    location: str | None = None
    confidence: str = Field(default="medium", pattern="^(high|medium|low|conflicted|unsupported)$")
    verification_state: str = Field(default="needs_verification", pattern="^(verified|needs_verification|unsupported|conflicted)$")


class SourceTrustUpdate(BaseModel):
    source_trust: str = Field(pattern="^(official|primary|reputable|expert|community|unverified)$")


class TranslationUpdate(BaseModel):
    human_edited_myanmar: str = Field(min_length=1)


@router.post("", status_code=201)
def create_source(payload: SourceCreate) -> dict:
    normalized_url = str(payload.url).rstrip("/")
    duplicate = next(
        (source for source in store.sources.values() if source["url"].rstrip("/") == normalized_url),
        None,
    )
    if duplicate:
        return {"status": "duplicate_ignored", "source": duplicate}

    source_id = f"SRC-{uuid4().hex[:8].upper()}"
    source = {
        "id": source_id,
        "url": normalized_url,
        "note": payload.note,
        "status": "new",
        "processing_stage": "queued",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "original_text": None,
        "ai_summary": None,
        "myanmar_translation": None,
        "human_edited_myanmar": None,
        "approved_myanmar": None,
        "source_trust": "unverified",
        "claims": [],
        "critical_warnings": [],
    }
    store.sources[source_id] = source
    store.save_source(source)
    store.add_activity("source_added", source_id, "—", "new")
    return {"status": "queued", "source": source}


@router.get("")
def list_sources() -> dict:
    items = list(store.sources.values())
    return {"items": items, "total": len(items)}


@router.get("/{source_id}")
def get_source(source_id: str) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("/{source_id}/claims", status_code=201)
def add_claim(source_id: str, payload: ClaimCreate) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    claim = {
        "id": f"CLM-{uuid4().hex[:8].upper()}",
        "text": payload.text,
        "excerpt": payload.excerpt,
        "location": payload.location,
        "confidence": payload.confidence,
        "verification_state": payload.verification_state,
        "created_at": now_iso(),
    }
    source["claims"].append(claim)
    source["updated_at"] = now_iso()
    store.save_source(source)
    if payload.verification_state in {"unsupported", "conflicted"} and payload.confidence in {"low", "unsupported", "conflicted"}:
        warning = f"Claim {claim['id']} requires resolution before approval."
        if warning not in source["critical_warnings"]:
            source["critical_warnings"].append(warning)
    store.save_source(source)
    store.add_activity("claim_added", source_id, "claims_updated", "claims_updated")
    return claim


@router.patch("/{source_id}/translation")
def update_translation(source_id: str, payload: TranslationUpdate) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    previous = source.get("human_edited_myanmar")
    source["human_edited_myanmar"] = payload.human_edited_myanmar
    source["updated_at"] = now_iso()
    store.save_source(source)
    store.add_activity("translation_edited", source_id, previous or "empty", "human_edited")
    return source


@router.get("/{source_id}/trust-score")
def get_trust_score(source_id: str) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return calculate_trust(source)


@router.patch("/{source_id}/trust")
def update_source_trust(source_id: str, payload: SourceTrustUpdate) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    previous = source.get("source_trust", "unverified")
    source["source_trust"] = payload.source_trust
    source["updated_at"] = now_iso()
    store.save_source(source)
    store.add_activity("source_trust_updated", source_id, previous, payload.source_trust)
    return calculate_trust(source)
