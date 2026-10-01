from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg

from app.services.processing import advance
from app.store import now_iso, store

router = APIRouter()


class ProcessingCreate(BaseModel):
    source_id: str


@router.post("", status_code=202)
def create_processing_task(payload: ProcessingCreate) -> dict:
    store.refresh()
    source = store.sources.get(payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    existing = next(
        (task for task in store.tasks.values()
         if task["source_id"] == payload.source_id and task["status"] in {"queued", "running"}),
        None,
    )
    if existing:
        return existing

    task_id = f"TSK-{uuid4().hex[:8].upper()}"
    task = {
        "id": task_id,
        "source_id": payload.source_id,
        "stage": "queued",
        "progress": 0,
        "status": "queued",
        "retry_count": 0,
        "error": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    try:
        store.tasks[task_id] = task
        store.save_task(task)
    except psycopg.errors.UniqueViolation:
        store.refresh()
        existing = next(
            (item for item in store.tasks.values()
             if item["source_id"] == payload.source_id and item["status"] in {"queued", "running"}),
            None,
        )
        if existing:
            return existing
        raise
    previous = source.get("status", "new")
    source["status"] = "processing"
    source["processing_stage"] = "queued"
    source["updated_at"] = now_iso()
    store.save_source(source)
    store.add_activity("processing_started", payload.source_id, previous, "processing")
    return task


@router.get("")
def list_processing_tasks() -> dict:
    store.refresh()
    items = list(store.tasks.values())
    return {"items": items, "total": len(items)}


@router.get("/{task_id}")
def get_processing_task(task_id: str) -> dict:
    store.refresh()
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Processing task not found")
    return task


@router.post("/{task_id}/advance")
def advance_processing_task(task_id: str) -> dict:
    store.refresh()
    if task_id not in store.tasks:
        raise HTTPException(status_code=404, detail="Processing task not found")
    return advance(task_id)


@router.post("/{task_id}/retry")
def retry_processing_task(task_id: str) -> dict:
    store.refresh()
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Processing task not found")

    previous = task["stage"]
    task.update(
        {
            "retry_count": task["retry_count"] + 1,
            "error": None,
            "status": "queued",
            "stage": "queued",
            "progress": 0,
            "updated_at": now_iso(),
        }
    )
    source = store.sources.get(task["source_id"])
    if source:
        source["status"] = "processing"
        source["processing_stage"] = "queued"
        source["updated_at"] = now_iso()
        store.save_source(source)
    store.save_task(task)
    store.add_activity("processing_retry", task["source_id"], previous, "queued")
    return task
