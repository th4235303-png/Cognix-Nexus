"""Brain YouTube Tracker — REST endpoints for Cognix Nexus.

Endpoints:
  POST   /brain/youtube/channels             — add a YouTube channel
  GET    /brain/youtube/channels             — list all tracked channels
  DELETE /brain/youtube/channels/{channel_id} — remove channel
  GET    /brain/youtube/feed                 — list latest videos with summaries (paginated)
  POST   /brain/youtube/poll                 — manually trigger poll for all channels
  GET    /brain/youtube/status               — overall tracker status
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from app.ownership import owner_for_request
from app.services.youtube_tracker import (
    extract_channel_id,
    fetch_channel_feed,
    fetch_transcript,
    summarize_video,
)
from app.store import store

logger = logging.getLogger("cognix.youtube_tracker_router")

router = APIRouter(prefix="/brain/youtube", tags=["brain-youtube"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _db():
    if store.database is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "DB_REQUIRED", "message": "Persistent database is required for YouTube Tracker"},
        )
    return store.database


def _require_yt_tables(db) -> None:
    """Raise 503 if migration 043 hasn't been applied yet."""
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.youtube_channels') AS t")
                row = cur.fetchone()
        if row["t"] is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "MIGRATION_PENDING",
                    "message": (
                        "YouTube tracker tables not found. "
                        "Restart the server to apply migration 043_youtube_tracker.sql automatically."
                    ),
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "DB_ERROR", "message": str(exc)}) from exc


# ── request / response models ─────────────────────────────────────────────────

class ChannelAdd(BaseModel):
    channel_url: str = Field(min_length=1, max_length=500)
    poll_interval_hours: int = Field(default=6, ge=1, le=168)


# ── poll logic ────────────────────────────────────────────────────────────────

async def _poll_all_channels(db) -> dict:
    """Poll all active channels, insert new videos, fetch transcripts and summarize."""
    from app.services.llm import LLMProvider

    llm = LLMProvider()
    results = {"channels_polled": 0, "new_videos": 0, "errors": []}

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT channel_id, channel_name FROM youtube_channels WHERE is_active = TRUE"
                )
                channels = cur.fetchall()
    except Exception as exc:
        logger.error(f"Failed to fetch channels for polling: {exc}")
        results["errors"].append(str(exc))
        return results

    for ch in channels:
        channel_id = ch["channel_id"]
        channel_name = ch["channel_name"] or channel_id
        results["channels_polled"] += 1
        try:
            videos = fetch_channel_feed(channel_id)
        except Exception as exc:
            logger.error(f"Feed fetch failed for {channel_id}: {exc}")
            results["errors"].append(f"{channel_id}: feed fetch error — {exc}")
            continue

        for video in videos:
            video_id = video["video_id"]
            if not video_id:
                continue
            try:
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT id FROM brain_youtube_videos WHERE video_id = %s",
                            (video_id,),
                        )
                        existing = cur.fetchone()
                if existing:
                    continue

                # Parse published_at
                published_at = None
                if video.get("published_at"):
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(video["published_at"])
                    except Exception:
                        try:
                            published_at = datetime.fromisoformat(video["published_at"])
                        except Exception:
                            published_at = None

                # Insert stub record
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """INSERT INTO brain_youtube_videos
                               (channel_id, video_id, title, published_at)
                               VALUES (%s, %s, %s, %s)
                               ON CONFLICT (video_id) DO NOTHING""",
                            (channel_id, video_id, video.get("title", ""), published_at),
                        )
                    conn.commit()

                results["new_videos"] += 1

                # Fetch transcript (sync, run in thread)
                transcript = await asyncio.to_thread(fetch_transcript, video_id)

                transcript_fetched = transcript is not None
                summary_data = {"summary": "", "key_points": []}

                if transcript:
                    try:
                        summary_data = await summarize_video(video.get("title", ""), transcript, llm)
                    except Exception as exc:
                        logger.warning(f"LLM summarize failed for {video_id}: {exc}")

                # Update record with transcript and summary
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """UPDATE brain_youtube_videos
                               SET transcript_fetched = %s,
                                   transcript_text = %s,
                                   summary = %s,
                                   key_points = %s,
                                   llm_processed = %s
                               WHERE video_id = %s""",
                            (
                                transcript_fetched,
                                transcript,
                                summary_data.get("summary", ""),
                                Jsonb(summary_data.get("key_points", [])),
                                bool(summary_data.get("summary")),
                                video_id,
                            ),
                        )
                    conn.commit()

            except Exception as exc:
                logger.error(f"Error processing video {video_id}: {exc}")
                results["errors"].append(f"{video_id}: {exc}")

        # Update last_polled_at
        try:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE youtube_channels SET last_polled_at = NOW() WHERE channel_id = %s",
                        (channel_id,),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to update last_polled_at for {channel_id}: {exc}")

    return results


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/channels", status_code=201)
def add_channel(payload: ChannelAdd, request: Request) -> dict:
    """Add a YouTube channel to track."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    channel_id = extract_channel_id(payload.channel_url)
    if not channel_id:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_CHANNEL_URL",
                "message": (
                    "Could not extract a YouTube channel ID from the provided URL. "
                    "Use a direct channel URL (youtube.com/channel/UCxxx) or a raw channel ID (UCxxx...)."
                ),
            },
        )

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO youtube_channels (channel_id, channel_url, poll_interval_hours)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (channel_id) DO UPDATE
                         SET channel_url = EXCLUDED.channel_url,
                             poll_interval_hours = EXCLUDED.poll_interval_hours,
                             is_active = TRUE
                       RETURNING *""",
                    (channel_id, payload.channel_url, payload.poll_interval_hours),
                )
                row = cur.fetchone()
            conn.commit()
        return {"status": "ok", "channel": dict(row)}
    except Exception as exc:
        logger.exception("add_channel failed")
        raise HTTPException(status_code=500, detail={"code": "INSERT_ERROR", "message": str(exc)}) from exc


@router.get("/channels")
def list_channels(request: Request) -> dict:
    """List all tracked YouTube channels."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT yc.*,
                              COUNT(v.id) AS video_count
                       FROM youtube_channels yc
                       LEFT JOIN brain_youtube_videos v ON v.channel_id = yc.channel_id
                       GROUP BY yc.id
                       ORDER BY yc.created_at DESC"""
                )
                rows = cur.fetchall()
        channels = [dict(r) for r in rows]
        return {"channels": channels, "total": len(channels)}
    except Exception as exc:
        logger.exception("list_channels failed")
        raise HTTPException(status_code=500, detail={"code": "READ_ERROR", "message": str(exc)}) from exc


@router.delete("/channels/{channel_id}", status_code=200)
def remove_channel(channel_id: str, request: Request) -> dict:
    """Remove a tracked YouTube channel (and cascade-delete its videos)."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM youtube_channels WHERE channel_id = %s RETURNING channel_id",
                    (channel_id,),
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Channel not found"})
        return {"status": "deleted", "channel_id": channel_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("remove_channel failed")
        raise HTTPException(status_code=500, detail={"code": "DELETE_ERROR", "message": str(exc)}) from exc


@router.get("/feed")
def get_feed(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    channel_id: str | None = Query(default=None),
) -> dict:
    """List latest videos with summaries, optionally filtered by channel_id."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                if channel_id:
                    cur.execute(
                        "SELECT COUNT(*) AS total FROM brain_youtube_videos WHERE channel_id = %s",
                        (channel_id,),
                    )
                    total = int(cur.fetchone()["total"])
                    cur.execute(
                        """SELECT v.*, yc.channel_name
                           FROM brain_youtube_videos v
                           JOIN youtube_channels yc ON yc.channel_id = v.channel_id
                           WHERE v.channel_id = %s
                           ORDER BY v.published_at DESC NULLS LAST
                           LIMIT %s OFFSET %s""",
                        (channel_id, limit, offset),
                    )
                else:
                    cur.execute("SELECT COUNT(*) AS total FROM brain_youtube_videos")
                    total = int(cur.fetchone()["total"])
                    cur.execute(
                        """SELECT v.*, yc.channel_name
                           FROM brain_youtube_videos v
                           JOIN youtube_channels yc ON yc.channel_id = v.channel_id
                           ORDER BY v.published_at DESC NULLS LAST
                           LIMIT %s OFFSET %s""",
                        (limit, offset),
                    )
                rows = cur.fetchall()
        videos = [dict(r) for r in rows]
        return {"videos": videos, "total": total, "limit": limit, "offset": offset}
    except Exception as exc:
        logger.exception("get_feed failed")
        raise HTTPException(status_code=500, detail={"code": "READ_ERROR", "message": str(exc)}) from exc


@router.post("/poll")
async def poll_channels(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Manually trigger a poll for all active channels (runs in background)."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    async def _bg_poll():
        try:
            result = await _poll_all_channels(db)
            logger.info(f"YouTube poll completed: {result}")
        except Exception as exc:
            logger.error(f"YouTube background poll failed: {exc}")

    asyncio.create_task(_bg_poll())
    return {"status": "polling_started", "message": "Poll triggered for all active channels in background"}


@router.get("/status")
def get_status(request: Request) -> dict:
    """Return overall tracker status summary."""
    owner_for_request(request)
    db = _db()
    _require_yt_tables(db)

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS total FROM youtube_channels")
                total_channels = int(cur.fetchone()["total"])

                cur.execute("SELECT COUNT(*) AS total FROM youtube_channels WHERE is_active = TRUE")
                active_channels = int(cur.fetchone()["total"])

                cur.execute("SELECT COUNT(*) AS total FROM brain_youtube_videos")
                total_videos = int(cur.fetchone()["total"])

                cur.execute(
                    "SELECT COUNT(*) AS total FROM brain_youtube_videos WHERE transcript_fetched = TRUE"
                )
                transcribed_videos = int(cur.fetchone()["total"])

                cur.execute(
                    "SELECT COUNT(*) AS total FROM brain_youtube_videos WHERE llm_processed = TRUE"
                )
                processed_videos = int(cur.fetchone()["total"])

                cur.execute(
                    "SELECT MAX(last_polled_at) AS last_poll FROM youtube_channels"
                )
                last_poll_row = cur.fetchone()
                last_polled_at = last_poll_row["last_poll"] if last_poll_row else None

        return {
            "status": "ok",
            "total_channels": total_channels,
            "active_channels": active_channels,
            "total_videos": total_videos,
            "transcribed_videos": transcribed_videos,
            "llm_processed_videos": processed_videos,
            "last_polled_at": last_polled_at.isoformat() if last_polled_at else None,
        }
    except Exception as exc:
        logger.exception("get_status failed")
        raise HTTPException(status_code=500, detail={"code": "READ_ERROR", "message": str(exc)}) from exc
