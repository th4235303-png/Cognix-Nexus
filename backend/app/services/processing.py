from app.store import store

STAGES = ("queued","extracting","cleaning","translating","summarizing","key_points","fact_check","trust_scoring","needs_review","approved")

def advance(task_id: str) -> dict:
    task = store.tasks[task_id]
    index = STAGES.index(task["stage"])
    next_stage = STAGES[min(index + 1, len(STAGES) - 1)]
    task["stage"] = next_stage
    task["progress"] = round((STAGES.index(next_stage) / (len(STAGES) - 1)) * 100)
    task["status"] = "completed" if next_stage in {"needs_review", "approved"} else "running"
    source = store.sources.get(task["source_id"])
    if source:
        source["processing_stage"] = next_stage
        if next_stage == "needs_review": source["status"] = "needs_review"
        elif next_stage == "approved": source["status"] = "approved"
    return task
