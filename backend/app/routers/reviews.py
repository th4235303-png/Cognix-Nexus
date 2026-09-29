from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.store import store

router = APIRouter()


class ReviewAction(BaseModel):
    note: str | None = None


@router.get("")
def list_reviews() -> dict:
    items = list(store.reviews.values())
    return {"items": items, "total": len(items)}


@router.post("/{source_id}/approve")
def approve_review(source_id: str, action: ReviewAction) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    critical = source.get("critical_warnings", [])
    if critical:
        raise HTTPException(status_code=409, detail={"code": "CRITICAL_WARNINGS", "warnings": critical})
    review = {"source_id": source_id, "status": "approved", "note": action.note}
    store.reviews[source_id] = review
    previous = source.get("status", "needs_review")
    source["status"] = "approved"
    source["processing_stage"] = "approved"
    store.add_activity("approved", source_id, previous, "approved")
    return review


@router.post("/{source_id}/revision")
def request_revision(source_id: str, action: ReviewAction) -> dict:
    source = store.sources.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    review = {"source_id": source_id, "status": "revision_requested", "note": action.note}
    store.reviews[source_id] = review
    previous = source.get("status", "needs_review")
    source["status"] = "needs_review"
    store.add_activity("revision_requested", source_id, previous, "needs_review")
    return review
