from fastapi import APIRouter
from app.store import store

router = APIRouter()

@router.get("")
def list_activity() -> dict:
    store.refresh()
    return {"items": store.activity, "total": len(store.activity)}
