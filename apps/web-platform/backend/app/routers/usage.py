from fastapi import APIRouter
from app.store import store

router = APIRouter()

@router.get("")
def get_usage() -> dict:
    store.refresh()
    from app.services.ai_usage_tracker import get_ai_usage_summary
    ai_summary = get_ai_usage_summary("Cognix-Nexus")
    return {
        "ai_requests_today": ai_summary.get("total_calls_today", 0),
        "processing_jobs": len(store.tasks),
        "translation_requests": sum(1 for task in store.tasks.values() if task.get("stage") == "translating"),
        "drive_exports": len(store.exports),
        "ai_summary": ai_summary,
    }


@router.get("/ai")
def get_ai_usage() -> dict:
    """Consolidated endpoint for AI usage, quotas, and active provider chains."""
    from app.services.ai_usage_tracker import get_ai_usage_summary
    return get_ai_usage_summary("Cognix-Nexus")

