from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.logixa_flow import deliver
from app.store import store

router = APIRouter()


class DeliveryRequest(BaseModel):
    source_id: str


@router.post("/logixa-flow")
def deliver_to_logixa_flow(payload: DeliveryRequest) -> dict:
    store.refresh()
    source = store.sources.get(payload.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Only approved sources can be delivered")
    try:
        result = deliver({
            "event": "approved_knowledge",
            "source": {
                "id": source["id"],
                "url": source["url"],
                "summary": source.get("ai_summary"),
                "myanmar_translation": source.get("approved_myanmar") or source.get("human_edited_myanmar") or source.get("myanmar_translation"),
                "claims": source.get("claims", []),
                "trust": source.get("source_trust"),
            },
        })
    except Exception as exc:
        store.add_activity("logixa_delivery_failed", payload.source_id, "approved", "delivery_failed")
        raise HTTPException(status_code=502, detail={"code": "DELIVERY_FAILED", "message": str(exc)}) from exc
    store.add_activity("logixa_delivery_completed", payload.source_id, "approved", "delivered")
    return result
