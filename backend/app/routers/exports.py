from datetime import date
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.google_drive import build_export_package, upload_export
from app.store import store

router = APIRouter()


class DriveExportRequest(BaseModel):
    source_id: str
    idempotency_key: str


@router.post("/google-drive", status_code=202)
def export_to_google_drive(payload: DriveExportRequest) -> dict:
    store.refresh()
    source = store.sources.get(payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved sources can be exported")
    existing_id = store.export_keys.get(payload.idempotency_key)
    if existing_id:
        return store.exports[existing_id]
    export_id = f"EXP-{uuid4().hex[:8].upper()}"
    package = build_export_package(payload.source_id, date.today().isoformat())
    job = {
        "id": export_id,
        "source_id": payload.source_id,
        "status": "queued",
        "idempotency_key": payload.idempotency_key,
        "drive_reference": None,
        "files": list(package.files),
    }
    saved = store.create_export_if_absent(job)
    if saved["id"] != export_id:
        return saved
    store.add_activity("drive_export_queued", payload.source_id, "approved", "export_queued")
    return saved


@router.get("")
def list_exports() -> dict:
    store.refresh()
    items = list(store.exports.values())
    return {"items": items, "total": len(items)}


@router.get("/{export_id}")
def get_export(export_id: str) -> dict:
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    return job


@router.post("/{export_id}/retry")
def retry_export(export_id: str) -> dict:
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    if job["status"] not in {"failed", "retry_pending"}:
        raise HTTPException(status_code=409, detail=f"Export cannot retry from {job['status']}")
    previous = job["status"]
    job["status"] = "queued"
    store.save_export(job)
    store.add_activity("drive_export_retry_queued", job["source_id"], previous, "queued")
    return job


@router.post("/{export_id}/advance")
def advance_export(export_id: str) -> dict:
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    if job["status"] == "queued":
        previous = job["status"]
        job["status"] = "uploading"
    elif job["status"] == "uploading":
        previous = job["status"]
        source = store.sources.get(job["source_id"])
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        try:
            job["drive_reference"] = upload_export(source, build_export_package(source["id"], date.today().isoformat()))
            job["status"] = "exported"
            job["error"] = None
        except Exception as exc:
            job["status"] = "failed"
            job["error"] = str(exc)
    elif job["status"] == "exported":
        return job
    else:
        raise HTTPException(status_code=409, detail=f"Export cannot advance from {job['status']}")
    store.save_export(job)
    store.add_activity("drive_export_state_changed", job["source_id"], previous, job["status"])
    return job
