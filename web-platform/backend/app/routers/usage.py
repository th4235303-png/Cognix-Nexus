from fastapi import APIRouter
from app.store import store

router = APIRouter()

@router.get("")
def get_usage() -> dict:
    store.refresh()
    return {
        "ai_requests_today": 0,
        "processing_jobs": len(store.tasks),
        "translation_requests": sum(1 for task in store.tasks.values() if task.get("stage") == "translating"),
        "drive_exports": len(store.exports),
    }
