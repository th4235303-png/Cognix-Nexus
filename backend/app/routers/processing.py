from fastapi import APIRouter

router = APIRouter()


@router.post("")
def create_processing_task(source_id: str) -> dict:
    return {"task_id": f"TSK-{source_id}", "status": "queued"}


@router.get("")
def list_processing_tasks() -> dict:
    return {"items": [], "total": 0}


@router.get("/{task_id}")
def get_processing_task(task_id: str) -> dict:
    return {"id": task_id, "status": "queued", "progress": 0}
