from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DriveExportRequest(BaseModel):
    source_id: str
    idempotency_key: str


@router.post("/google-drive")
def export_to_google_drive(payload: DriveExportRequest) -> dict:
    return {
        "export_id": f"EXP-{payload.source_id}",
        "status": "queued",
        "source_id": payload.source_id,
        "idempotency_key": payload.idempotency_key,
    }


@router.get("/{export_id}")
def get_export(export_id: str) -> dict:
    return {"id": export_id, "status": "queued"}
