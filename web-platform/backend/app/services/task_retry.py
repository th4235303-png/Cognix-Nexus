from __future__ import annotations

from datetime import datetime, timezone


MAX_PROCESSING_RETRIES = 5
RETRY_BASE_DELAY_SECONDS = 5
RETRY_MAX_DELAY_SECONDS = 300


def retry_delay_seconds(retry_count: int) -> int:
    if retry_count <= 0:
        return 0
    return min(RETRY_MAX_DELAY_SECONDS, RETRY_BASE_DELAY_SECONDS * (2 ** min(retry_count - 1, 6)))


def retry_ready(task: dict, now: datetime | None = None) -> bool:
    if task.get("status") != "queued":
        return True
    delay = retry_delay_seconds(int(task.get("retry_count", 0)))
    if not delay:
        return True
    try:
        updated = datetime.fromisoformat(task["updated_at"])
    except (KeyError, TypeError, ValueError):
        return True
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    return (current - updated).total_seconds() >= delay


def task_is_runnable(task: dict, now: datetime | None = None) -> bool:
    return (
        task.get("status") in {"queued", "running"}
        and task.get("stage") not in {"needs_review", "approved"}
        and retry_ready(task, now)
    )
