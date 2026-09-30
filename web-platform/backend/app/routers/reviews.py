from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.store import now_iso, store

router = APIRouter()


class ReviewAction(BaseModel):
    note: str | None = None


@router.get("")
def list_reviews() -> dict:
    store.refresh()
    items = list(store.reviews.values())
    return {"items": items, "total": len(items)}


@router.post("/{source_id}/approve")
def approve_review(source_id: str, action: ReviewAction) -> dict:
    store.refresh()
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    critical = source.get("critical_warnings", [])
    if critical:
        raise HTTPException(status_code=409, detail={"code": "CRITICAL_WARNINGS", "warnings": critical})
    approved_text = source.get("human_edited_myanmar") or source.get("myanmar_translation")
    if not approved_text:
        raise HTTPException(status_code=409, detail={"code": "MISSING_TRANSLATION", "message": "A Myanmar translation is required before approval"})
    review = {"source_id": source_id, "status": "approved", "note": action.note}
    review["created_at"] = now_iso()
    store.reviews[source_id] = review
    store.save_review(review)
    previous = source.get("status", "needs_review")
    source["status"] = "approved"
    source["processing_stage"] = "approved"
    source["approved_myanmar"] = approved_text
    source["updated_at"] = now_iso()
    store.save_source(source)
    store.add_activity("approved", source_id, previous, "approved")
    return review


@router.post("/{source_id}/revision")
def request_revision(source_id: str, action: ReviewAction) -> dict:
    store.refresh()
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    review = {"source_id": source_id, "status": "revision_requested", "note": action.note}
    review["created_at"] = now_iso()
    store.reviews[source_id] = review
    store.save_review(review)
    previous = source.get("status", "needs_review")
    source["status"] = "needs_review"
    store.save_source(source)
    store.add_activity("revision_requested", source_id, previous, "needs_review")
    return review
