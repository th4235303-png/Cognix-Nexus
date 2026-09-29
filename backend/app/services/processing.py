from app.store import now_iso, store

STAGES = (
    "queued",
    "extracting",
    "cleaning",
    "translating",
    "summarizing",
    "key_points",
    "fact_check",
    "trust_scoring",
    "needs_review",
    "approved",
)


def advance(task_id: str) -> dict:
    task = store.tasks[task_id]
    current_stage = task["stage"]
    index = STAGES.index(current_stage)
    next_stage = STAGES[min(index + 1, len(STAGES) - 1)]
    task["stage"] = next_stage
    task["progress"] = round((STAGES.index(next_stage) / (len(STAGES) - 1)) * 100)
    task["status"] = "completed" if next_stage in {"needs_review", "approved"} else "running"
    task["updated_at"] = now_iso()
    task["error"] = None

    source = store.sources.get(task["source_id"])
    if source:
        previous = source.get("processing_stage", current_stage)
        source["processing_stage"] = next_stage
        if next_stage == "needs_review":
            source["status"] = "needs_review"
        elif next_stage == "approved":
            source["status"] = "approved"
        store.add_activity(
            "processing_stage_advanced",
            task["source_id"],
            previous,
            next_stage,
        )
    return task
