from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_usage() -> dict:
    return {
        "ai_requests_today": 0,
        "processing_jobs": 0,
        "translation_requests": 0,
        "drive_exports": 0,
    }
