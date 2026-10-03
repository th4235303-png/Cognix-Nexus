from __future__ import annotations

from datetime import date

from app.services.google_drive import build_export_package, upload_export
from app.store import store


def advance_export_job(export_id: str) -> dict:
    db = store.database
    if db is not None and not db.try_claim_task(f"export:{export_id}"):
        store.refresh()
        job = store.exports.get(export_id)
        if not job:
            raise KeyError("Export not found")
        return job
    try:
        store.refresh()
        job = store.exports.get(export_id)
        if not job:
            raise KeyError("Export not found")
        if job["status"] == "queued":
            previous = job["status"]
            job["status"] = "uploading"
            store.save_export(job)
        elif job["status"] == "uploading":
            previous = job["status"]
            source = store.sources.get(job["source_id"])
            if not source:
                raise KeyError("Source not found")
            try:
                job["drive_reference"] = upload_export(
                    source,
                    build_export_package(source["id"], date.today().isoformat()),
                )
                job["status"] = "exported"
                job["error"] = None
            except Exception as exc:
                job["status"] = "failed"
                job["error"] = type(exc).__name__
        elif job["status"] == "exported":
            return job
        else:
            raise ValueError(f"Export cannot advance from {job['status']}")
        store.save_export(job)
        store.add_activity("drive_export_state_changed", job["source_id"], previous, job["status"])
        return job
    finally:
        if db is not None:
            db.release_task(f"export:{export_id}")
