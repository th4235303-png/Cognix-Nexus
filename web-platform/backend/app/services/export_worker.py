from __future__ import annotations

import logging

from app.services.lease_runner import LeaseLostError, run_with_lease_heartbeat
from app.store import store

logger = logging.getLogger("cognix.worker")


def advance_export_job(export_id: str) -> dict:
    db = store.database
    if db is None:
        job = store.exports.get(export_id)
        if not job:
            raise KeyError(export_id)
        if job["status"] == "queued":
            job["status"] = "uploading"
            store.save_export(job)
            return job
        if job["status"] == "uploading":
            source = store.sources.get(job["source_id"])
            if not source:
                raise RuntimeError("Source not found")
            job["status"] = "exported"
            job["result_url"] = source.get("url")
            store.save_export(job)
            return job
        return job

    claimed = db.claim_export_job(export_id)
    if claimed is None:
        store.refresh()
        job = store.exports.get(export_id)
        if not job:
            raise KeyError(export_id)
        if job.get("status") in {"exported", "failed"}:
            return job
        logger.info("export_job_claim_skipped export_id=%s", export_id)
        return job
    row, token = claimed
    logger.info("export_job_claimed export_id=%s status=%s", export_id, row["status"])
    try:
        if row["status"] == "queued":
            changed = db.transition_export_job(
                export_id, token, "queued", "uploading"
            )
            if changed is None:
                raise LeaseLostError(f"Export lease lost before upload stage: {export_id}")
            store.refresh()
            logger.info("export_job_upload_started export_id=%s", export_id)
            return store.exports.get(export_id) or changed

        def upload(lease_is_valid):
            try:
                store.refresh()
                job = store.exports.get(export_id)
                source = store.sources.get(job["source_id"]) if job else None
                if not source:
                    raise RuntimeError("Source not found")
                if not lease_is_valid():
                    raise LeaseLostError(f"Export lease lost before upload: {export_id}")
                result_url = source.get("url")
                changed = db.transition_export_job(
                    export_id,
                    token,
                    "uploading",
                    "exported",
                    drive_reference=result_url,
                )
                if changed is None:
                    raise LeaseLostError(f"Export lease lost before completion: {export_id}")
                store.refresh()
                logger.info("export_job_exported export_id=%s", export_id)
                return store.exports.get(export_id) or changed
            except LeaseLostError:
                raise
            except Exception as exc:
                if not lease_is_valid():
                    raise LeaseLostError(f"Export lease lost before failure persistence: {export_id}") from exc
                changed = db.transition_export_job(
                    export_id,
                    token,
                    "uploading",
                    "failed",
                    error=str(exc),
                )
                if changed is None:
                    raise LeaseLostError(f"Export lease lost before failure persistence: {export_id}") from exc
                store.refresh()
                logger.warning(
                    "export_job_failed export_id=%s error_type=%s",
                    export_id,
                    type(exc).__name__,
                )
                return store.exports.get(export_id) or changed

        return run_with_lease_heartbeat(
            "export_job",
            export_id,
            lambda: db.renew_export_job_claim(export_id, token),
            upload,
        )
    except LeaseLostError:
        logger.warning("export_job_lease_lost export_id=%s", export_id)
        store.refresh()
        return store.exports.get(export_id) or {"id": export_id, "status": "uploading"}
    finally:
        db.release_export_job_claim(export_id, token)
