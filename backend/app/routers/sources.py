from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

router = APIRouter()


class SourceCreate(BaseModel):
    url: HttpUrl
    note: str | None = None


@router.post("")
def create_source(payload: SourceCreate) -> dict:
    return {"status": "queued", "source": payload.model_dump(mode="json")}


@router.get("")
def list_sources() -> dict:
    return {"items": [], "total": 0}


@router.get("/{source_id}")
def get_source(source_id: str) -> dict:
    return {"id": source_id, "status": "not_connected"}
