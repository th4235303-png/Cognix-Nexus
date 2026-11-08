from datetime import date
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.ownership import get_source_for_request, owner_for_request
from app.services.google_drive import build_export_package
from app.services.google_drive_package import build_file_contents
from app.services.export_worker import advance_export_job
from app.store import store

router = APIRouter()


class DriveExportRequest(BaseModel):
    source_id: str
    idempotency_key: str


@router.get("/local/{source_id}")
def export_to_local_json(source_id: str, request: Request) -> Response:
    """Download an owner-scoped, approved source package without any cloud provider."""
    owner_for_request(request)
    store.refresh()
    source = get_source_for_request(request, source_id)
    if source.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved sources can be exported")
    files = build_export_package(source_id, date.today().isoformat()).files
    contents = build_file_contents(source)
    package = {
        "export_version": "1.0.0",
        "source_app": "Cognix Nexus",
        "exported_at": date.today().isoformat(),
        "source_id": source_id,
        "files": {name: {"content": contents[name][0], "content_type": contents[name][1]} for name in files},
    }
    store.add_activity("local_export_downloaded", source_id, "approved", "manual_export")
    return Response(
        content=json.dumps(package, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="cognix-source-{source_id}.json"'},
    )


@router.post("/google-drive", status_code=202)
def export_to_google_drive(payload: DriveExportRequest, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    source = get_source_for_request(request, payload.source_id)
    if source.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved sources can be exported")
    existing_id = store.export_keys.get(payload.idempotency_key)
    if existing_id:
        existing = store.exports[existing_id]
        if existing["source_id"] != payload.source_id:
            raise HTTPException(status_code=409, detail="Idempotency key is already in use")
        if existing.get("status") == "failed":
            return existing
        return existing
    export_id = f"EXP-{uuid4().hex[:8].upper()}"
    package = build_export_package(payload.source_id, date.today().isoformat())
    job = {
        "id": export_id,
        "source_id": payload.source_id,
        "status": "queued",
        "idempotency_key": payload.idempotency_key,
        "drive_reference": None,
        "files": list(package.files),
        "error": None,
    }
    saved = store.create_export_if_absent(job)
    if saved["id"] != export_id:
        return saved
    store.add_activity("drive_export_queued", payload.source_id, "approved", "export_queued")
    return saved


@router.get("")
def list_exports(request: Request) -> dict:
    owner_id = owner_for_request(request)
    store.refresh()
    source_ids = {
        source["id"] for source in store.list_sources_for_owner(owner_id)
    }
    items = [job for job in store.exports.values() if job["source_id"] in source_ids]
    return {"items": items, "total": len(items)}


@router.get("/{export_id}")
def get_export(export_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    get_source_for_request(request, job["source_id"])
    return job


@router.post("/{export_id}/retry")
def retry_export(export_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    get_source_for_request(request, job["source_id"])
    if job["status"] not in {"failed", "retry_pending"}:
        raise HTTPException(status_code=409, detail=f"Export cannot retry from {job['status']}")
    previous = job["status"]
    job["status"] = "queued"
    store.save_export(job)
    store.add_activity("drive_export_retry_queued", job["source_id"], previous, "queued")
    return job


@router.post("/{export_id}/advance")
def advance_export(export_id: str, request: Request) -> dict:
    owner_for_request(request)
    store.refresh()
    job = store.exports.get(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export not found")
    get_source_for_request(request, job["source_id"])
    try:
        return advance_export_job(export_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
