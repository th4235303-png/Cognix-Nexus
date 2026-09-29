from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_activity() -> dict:
    return {"items": [], "total": 0}
