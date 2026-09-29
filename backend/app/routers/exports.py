from datetime import date
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.google_drive import build_export_package
from app.store import store

router = APIRouter()


class DriveExportRequest(BaseModel):
    source_id: str
    idempotency_key: str


@router.post("/google-drive", status_code=202)
def export_to_google_drive(payload: DriveExportRequest) -> dict:
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
    store.exports[export_id] = job
    store.export_keys[payload.idempotency_key] = export_id
    store.add_activity("drive_export_queued", payload.source_id, "approved", "export_queued")
    return job


@router.get("/{export_id}")
def get_export(export_id: str) -> dict:
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    return job
