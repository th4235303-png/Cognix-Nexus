from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.store import store

router = APIRouter()


class ProcessingCreate(BaseModel):
    source_id: str


@router.post("", status_code=202)
def create_processing_task(payload: ProcessingCreate) -> dict:
    source = store.sources.get(payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    task_id = f"TSK-{uuid4().hex[:8].upper()}"
    task = {
        "id": task_id,
        "source_id": payload.source_id,
        "stage": "queued",
        "progress": 0,
        "status": "queued",
        "retry_count": 0,
        "error": None,
    }
    store.tasks[task_id] = task
    source["status"] = "processing"
    source["processing_stage"] = "queued"
    store.add_activity("processing_started", payload.source_id, "new", "processing")
    return task


@router.get("")
def list_processing_tasks() -> dict:
    items = list(store.tasks.values())
    return {"items": items, "total": len(items)}


@router.get("/{task_id}")
def get_processing_task(task_id: str) -> dict:
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Processing task not found")
    return task
