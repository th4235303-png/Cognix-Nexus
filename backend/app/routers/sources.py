from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.store import now_iso, store

router = APIRouter()


class SourceCreate(BaseModel):
    url: HttpUrl
    note: str | None = None


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
