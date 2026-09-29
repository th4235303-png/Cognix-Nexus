from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ReviewAction(BaseModel):
    note: str | None = None


@router.get("")
def list_reviews() -> dict:
    return {"items": [], "total": 0}


@router.post("/{source_id}/approve")
def approve_review(source_id: str, action: ReviewAction) -> dict:
    return {"source_id": source_id, "status": "approved", "note": action.note}


@router.post("/{source_id}/revision")
def request_revision(source_id: str, action: ReviewAction) -> dict:
    return {"source_id": source_id, "status": "revision_requested", "note": action.note}
