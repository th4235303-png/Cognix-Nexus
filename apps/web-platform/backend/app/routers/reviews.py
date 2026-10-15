from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.ownership import get_source_for_request, owner_for_request
from app.store import now_iso, store

router = APIRouter()


class ReviewAction(BaseModel):
    note: str | None = None


@router.get("")
def list_reviews(request: Request) -> dict:
    owner_id = owner_for_request(request)
    store.refresh()
    source_ids = {
        source["id"] for source in store.list_sources_for_owner(owner_id)
    }
    items = [review for source_id, review in store.reviews.items() if source_id in source_ids]
    return {"items": items, "total": len(items)}


@router.post("/{source_id}/approve")
def approve_review(source_id: str, action: ReviewAction, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    source = get_source_for_request(request, source_id)
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
def request_revision(source_id: str, action: ReviewAction, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    source = get_source_for_request(request, source_id)
    review = {"source_id": source_id, "status": "revision_requested", "note": action.note}
    review["created_at"] = now_iso()
    store.reviews[source_id] = review
    store.save_review(review)
    previous = source.get("status", "needs_review")
    source["status"] = "needs_review"
    store.save_source(source)
    store.add_activity("revision_requested", source_id, previous, "needs_review")
    return review
