from uuid import uuid4
from copy import deepcopy

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import psycopg

from app.ownership import get_source_for_request, get_task_for_request, owner_for_request
from app.services.processing import TaskLeaseLost, advance
from app.services.task_retry import MAX_PROCESSING_RETRIES
from app.store import now_iso, store

router = APIRouter()


class ProcessingCreate(BaseModel):
    source_id: str


@router.post("", status_code=202)
def create_processing_task(payload: ProcessingCreate, request: Request) -> dict:
    owner_id = owner_for_request(request)
    store.refresh()
    source = get_source_for_request(request, payload.source_id)
    existing = next(
        (task for task in store.list_tasks_for_owner(owner_id)
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
            (item for item in store.list_tasks_for_owner(owner_id)
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
def list_processing_tasks(request: Request) -> dict:
    owner_id = owner_for_request(request)
    store.refresh()
    items = store.list_tasks_for_owner(owner_id)
    return {"items": items, "total": len(items)}


@router.get("/{task_id}")
def get_processing_task(task_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    return get_task_for_request(request, task_id)


@router.post("/{task_id}/advance")
def advance_processing_task(task_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    task = get_task_for_request(request, task_id)
    if task["status"] in {"completed", "failed"} or task["stage"] == "needs_review":
        return advance(task_id)
    if store.database is None:
        return advance(task_id)
    claim_token = store.database.claim_task(task_id)
    if claim_token is None:
        raise HTTPException(status_code=409, detail="Processing task is not currently claimable")
    try:
        return advance(task_id, claim_token=claim_token)
    except TaskLeaseLost as exc:
        raise HTTPException(status_code=409, detail="Processing task is currently leased by a worker") from exc
    finally:
        store.database.release_task(task_id, claim_token)


@router.post("/{task_id}/retry")
def retry_processing_task(task_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    task = get_task_for_request(request, task_id)
    if task["status"] == "completed":
        raise HTTPException(status_code=409, detail="Completed processing tasks cannot be retried")
    if task["retry_count"] >= MAX_PROCESSING_RETRIES:
        raise HTTPException(
            status_code=409,
            detail={"code": "RETRY_LIMIT_REACHED", "message": "Processing task retry limit has been reached"},
        )

    previous = task["stage"]
    previous_status = task["status"]
    task = deepcopy(task)
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
        source = deepcopy(source)
        source["status"] = "processing"
        source["processing_stage"] = "queued"
        source["updated_at"] = now_iso()
        if not store.save_processing_transition(
            task, source, previous_status, previous
        ):
            raise HTTPException(status_code=409, detail="Processing task is currently leased by a worker")
    else:
        raise HTTPException(status_code=404, detail="Source not found")
    store.add_activity("processing_retry", task["source_id"], previous, "queued")
    return task
