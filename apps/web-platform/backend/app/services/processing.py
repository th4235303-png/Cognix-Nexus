from hashlib import sha256
from copy import deepcopy
from collections.abc import Callable

from fastapi import HTTPException

from app.services.research_processor import ProcessingResult, process_stage
from app.services.task_retry import MAX_PROCESSING_RETRIES
from app.store import now_iso, store

STAGES = (
    "queued", "extracting", "cleaning", "translating", "summarizing",
    "key_points", "fact_check", "trust_scoring", "needs_review", "approved",
)
class TaskLeaseLost(RuntimeError):
    """Raised when a worker no longer owns the task lease at persistence time."""



def _apply_result(source: dict, result: ProcessingResult) -> None:
    if result.original_text is not None:
        source["original_text"] = result.original_text
    if result.cleaned_text is not None:
        source["original_text"] = result.cleaned_text
    if result.summary is not None:
        source["ai_summary"] = result.summary
    if result.translation is not None:
        source["myanmar_translation"] = result.translation
    if result.key_points is not None:
        source["key_points"] = result.key_points
        if not source.get("claims"):
            source["claims"] = [
                {
                    "id": f"CLM-AUTO-{sha256((source['id'] + ':' + str(index + 1)).encode()).hexdigest()[:12].upper()}",
                    "text": point,
                    "excerpt": point,
                    "location": "AI key point",
                    "confidence": "medium",
                    "verification_state": "needs_verification",
                    "created_at": now_iso(),
                }
                for index, point in enumerate(result.key_points)
            ]


def _fact_check(source: dict) -> None:
    warnings = source.setdefault("critical_warnings", [])
    if not source.get("claims"):
        warning = "No claims have been extracted for verification."
        if warning not in warnings:
            warnings.append(warning)
    for claim in source.get("claims", []):
        if claim.get("verification_state") in {"unsupported", "conflicted"}:
            warning = f"Claim {claim.get('id', 'unknown')} requires resolution before approval."
            if warning not in warnings:
                warnings.append(warning)
    if source.get("ai_summary") and not source.get("original_text"):
        warning = "Summary exists without retained source text."
        if warning not in warnings:
            warnings.append(warning)


def advance(
    task_id: str,
    claim_token: str | None = None,
    lease_is_valid: Callable[[], bool] | None = None,
) -> dict:
    if task_id not in store.tasks:
        store.refresh()
    if store.tasks.get(task_id, {}).get("status") == "cancelled":
        raise TaskLeaseLost(f"Processing task {task_id} was superseded")
    task = deepcopy(store.tasks[task_id])
    current_stage = task["stage"]
    current_status = task["status"]
    if current_stage == "needs_review":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVIEW_REQUIRED",
                "message": "Processing tasks must be approved through the review endpoint.",
            },
        )
    if task["status"] == "completed":
        raise HTTPException(status_code=409, detail="Completed processing tasks cannot be advanced")
    if task["status"] == "failed":
        raise HTTPException(status_code=409, detail="Failed processing tasks must be retried")
    index = STAGES.index(current_stage)
    next_stage = STAGES[min(index + 1, len(STAGES) - 1)]
    source = store.sources.get(task["source_id"])
    if source is None:
        raise KeyError(f"Source {task['source_id']} not found")
    source = deepcopy(source)

    try:
        if next_stage in {"extracting", "cleaning", "summarizing", "translating", "key_points"}:
            _apply_result(source, process_stage(next_stage, source))
        elif next_stage == "fact_check":
            _fact_check(source)
        elif next_stage == "trust_scoring":
            source["trust_snapshot"] = {
                "source_trust": source.get("source_trust", "unverified"),
                "claims_count": len(source.get("claims", [])),
            }
        task["error"] = None
    except Exception as exc:
        task["error"] = f"Processing failed: {type(exc).__name__}"
        task["status"] = "failed"
        task["updated_at"] = now_iso()
        source["status"] = "failed"
        source["updated_at"] = now_iso()
        if lease_is_valid is not None and not lease_is_valid():
            raise TaskLeaseLost(f"Lease lost while processing task {task_id}") from exc
        if not store.save_processing_transition(
            task, source, current_status, current_stage, claim_token
        ):
            raise TaskLeaseLost(f"Lease lost while persisting task {task_id}") from exc
        store.add_activity("processing_failed", task["source_id"], current_stage, "failed")
        return task

    task["stage"] = next_stage
    task["progress"] = round((STAGES.index(next_stage) / (len(STAGES) - 1)) * 100)
    task["status"] = "completed" if next_stage in {"needs_review", "approved"} else "running"
    task["updated_at"] = now_iso()

    previous = source.get("processing_stage", current_stage)
    source["processing_stage"] = next_stage
    if next_stage == "needs_review":
        source["status"] = "needs_review"
    elif next_stage == "approved":
        source["status"] = "approved"
    source["updated_at"] = now_iso()
    if lease_is_valid is not None and not lease_is_valid():
        raise TaskLeaseLost(f"Lease lost while processing task {task_id}")
    if not store.save_processing_transition(
        task, source, current_status, current_stage, claim_token
    ):
        raise TaskLeaseLost(f"Lease lost while persisting task {task_id}")
    store.add_activity("processing_stage_advanced", task["source_id"], previous, next_stage)
    return task
