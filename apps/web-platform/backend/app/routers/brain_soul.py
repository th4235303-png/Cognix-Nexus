"""Brain Soul Layer — REST endpoints for Cognix Nexus.

Endpoints:
  GET    /brain/soul/context           — list Soul File entries
  POST   /brain/soul/context           — upsert entry
  DELETE /brain/soul/context/{key}     — delete entry
  GET    /brain/soul/context/prefix    — preview LLM system-prompt prefix
  GET    /brain/soul/syntheses         — list weekly synthesis snapshots
  POST   /brain/soul/synthesize        — manually trigger synthesis
  GET    /brain/soul/status            — health overview
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.store import store

logger = logging.getLogger("cognix.brain_soul")

router = APIRouter(prefix="/brain/soul", tags=["brain-soul"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _db():
    if store.database is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "DB_REQUIRED", "message": "Persistent database is required for Brain Soul"},
        )
    return store.database


def _require_soul_tables(db) -> None:
    """Raise 503 with clear message if migration hasn't been applied yet."""
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT to_regclass('public.brain_soul_context') AS t"
                )
                row = cur.fetchone()
        if row["t"] is None:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "MIGRATION_PENDING",
                    "message": (
                        "Brain soul tables not found. "
                        "Restart the server to apply migration 042_brain_soul.sql automatically."
                    ),
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "DB_ERROR", "message": str(exc)}) from exc


# ── request / response models ─────────────────────────────────────────────────

class ContextUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=4000)
    description: str = Field(default="", max_length=500)


class SynthesizeRequest(BaseModel):
    topic: str = Field(default="general", min_length=1, max_length=80)
    force: bool = False


# ── context endpoints ─────────────────────────────────────────────────────────

@router.get("/context")
def list_context(request: Request) -> dict:
    """Return all Soul File entries."""
    db = _db()
    _require_soul_tables(db)
    try:
        entries = db.soul_list_context()
        return {"entries": entries, "total": len(entries)}
    except Exception as exc:
        logger.exception("soul_list_context failed")
        raise HTTPException(status_code=500, detail={"code": "READ_ERROR", "message": str(exc)}) from exc


@router.post("/context", status_code=201)
def upsert_context(payload: ContextUpsert, request: Request) -> dict:
    """Insert or update a Soul File entry."""
    db = _db()
    _require_soul_tables(db)
    try:
        entry = db.soul_upsert_context(
            key=payload.key,
            value=payload.value,
            description=payload.description,
            updated_by="user",
        )
        return {"entry": entry}
    except Exception as exc:
        logger.exception("soul_upsert_context failed key=%s", payload.key)
        raise HTTPException(status_code=500, detail={"code": "WRITE_ERROR", "message": str(exc)}) from exc


@router.delete("/context/{key}", status_code=200)
def delete_context(key: str, request: Request) -> dict:
    """Delete a Soul File entry by key."""
    db = _db()
    _require_soul_tables(db)
    try:
        deleted = db.soul_delete_context(key)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": f"No soul context entry with key '{key}'"},
            )
        return {"deleted": True, "key": key}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("soul_delete_context failed key=%s", key)
        raise HTTPException(status_code=500, detail={"code": "DELETE_ERROR", "message": str(exc)}) from exc


@router.get("/context/prefix")
def preview_prefix(request: Request) -> dict:
    """Preview the LLM system-prompt prefix that Brain Soul would inject."""
    db = _db()
    _require_soul_tables(db)
    try:
        prefix = db.soul_build_system_prefix()
        return {"prefix": prefix, "empty": not bool(prefix.strip())}
    except Exception as exc:
        logger.exception("soul_build_system_prefix failed")
        raise HTTPException(status_code=500, detail={"code": "PREFIX_ERROR", "message": str(exc)}) from exc


# ── synthesis endpoints ───────────────────────────────────────────────────────

@router.get("/syntheses")
def list_syntheses(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """Return recent weekly synthesis snapshots."""
    db = _db()
    _require_soul_tables(db)
    try:
        snapshots = db.soul_list_syntheses(limit=limit)
        return {"syntheses": snapshots, "total": len(snapshots)}
    except Exception as exc:
        logger.exception("soul_list_syntheses failed")
        raise HTTPException(status_code=500, detail={"code": "READ_ERROR", "message": str(exc)}) from exc


@router.post("/synthesize", status_code=202)
async def trigger_synthesis(payload: SynthesizeRequest, request: Request) -> dict:
    """Manually trigger a weekly synthesis for the given topic.

    Reads notes/concepts from the knowledge graph, summarises them with the
    configured LLM provider, then saves a BrainSoulSynthesis snapshot.
    """
    db = _db()
    _require_soul_tables(db)

    now = datetime.now(timezone.utc)
    period_label = now.strftime("%Y-W%W")
    week_ago = now - timedelta(days=7)
    topic = payload.topic.strip() or "general"

    # ── gather recent knowledge items ────────────────────────────────────────
    try:
        items: list[str] = []
        item_ids: list = []
        with db.connect() as conn:
            with conn.cursor() as cur:
                # Brain notes from last 7 days
                cur.execute(
                    "SELECT id, title, summary FROM brain_notes "
                    "WHERE created_at >= %s "
                    "ORDER BY created_at DESC LIMIT 30",
                    (week_ago,),
                )
                for row in cur.fetchall():
                    snippet = (row.get("summary") or row.get("title") or "")[:250].replace("\n", " ")
                    items.append(f"[note] {row['title']}: {snippet}")
                    item_ids.append(f"note:{row['id']}")

                # Brain concepts from last 7 days (if table exists)
                try:
                    cur.execute(
                        "SELECT id, name, description FROM brain_concepts "
                        "WHERE created_at >= %s "
                        "ORDER BY created_at DESC LIMIT 20",
                        (week_ago,),
                    )
                    for row in cur.fetchall():
                        snippet = (row.get("description") or "")[:200].replace("\n", " ")
                        items.append(f"[concept] {row['name']}: {snippet}")
                        item_ids.append(f"concept:{row['id']}")
                except Exception:
                    pass  # brain_concepts table optional
    except Exception as exc:
        logger.exception("synthesize: failed to gather knowledge items")
        raise HTTPException(
            status_code=500,
            detail={"code": "GATHER_ERROR", "message": str(exc)},
        ) from exc

    if len(items) < 3:
        return {
            "status": "skipped",
            "reason": f"Only {len(items)} items found in the past 7 days (need ≥ 3)",
            "period_label": period_label,
            "topic": topic,
        }

    combined = "\n".join(items)
    system_prompt = (
        "You are a personal knowledge synthesis assistant. "
        "Your job is to analyse a set of notes and concepts the user captured this week, "
        "and write a concise synthesis (250–400 words) that covers:\n"
        "1. Key themes and ideas that emerged\n"
        "2. Connections or patterns between items\n"
        "3. One or two actionable next steps or questions to explore\n\n"
        "Write in clear, direct prose — no excessive bullet points. "
        "Be insightful, not merely descriptive."
    )
    user_prompt = (
        f"Topic filter: {topic}\n"
        f"Period: past 7 days ({period_label})\n"
        f"Item count: {len(items)}\n\n"
        f"Knowledge items:\n{combined}\n\n"
        "Write the weekly synthesis now."
    )

    # ── call LLM provider ────────────────────────────────────────────────────
    synthesis_text: str
    provider: str | None
    try:
        from app.services.llm import llm_provider
        synthesis_text = await llm_provider.complete(system_prompt, user_prompt)
        provider = llm_provider.last_provider or "unknown"
    except Exception as llm_exc:
        logger.warning(
            "synthesize: LLM failed — %s; using extractive fallback", llm_exc
        )
        # Extractive fallback — concatenate top items
        synthesis_text = "\n\n".join(
            f"• {item}" for item in items[:10]
        )
        provider = "extractive_fallback"

    if not synthesis_text.strip():
        raise HTTPException(
            status_code=500,
            detail={"code": "EMPTY_SYNTHESIS", "message": "LLM returned empty synthesis text"},
        )

    # ── persist ──────────────────────────────────────────────────────────────
    try:
        snapshot = db.soul_save_synthesis(
            period_label=period_label,
            period_start=week_ago,
            period_end=now,
            topic=topic,
            synthesis_text=synthesis_text,
            source_item_ids=item_ids,
            provider=provider,
            force=payload.force,
        )
    except Exception as exc:
        logger.exception("synthesize: failed to persist snapshot")
        raise HTTPException(
            status_code=500,
            detail={"code": "SAVE_ERROR", "message": str(exc)},
        ) from exc

    return {
        "status": "created",
        "synthesis": snapshot,
        "item_count": len(items),
        "provider": provider,
    }


# ── status endpoint ───────────────────────────────────────────────────────────

@router.get("/status")
def soul_status(request: Request) -> dict:
    """Health overview for the Brain Soul layer."""
    db = _db()
    tables_ready = False
    context_count = 0
    synthesis_count = 0
    latest_synthesis: str | None = None

    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT to_regclass('public.brain_soul_context') AS ctx, "
                    "       to_regclass('public.brain_soul_syntheses') AS syn"
                )
                row = cur.fetchone()
                tables_ready = row["ctx"] is not None and row["syn"] is not None

        if tables_ready:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) AS n FROM brain_soul_context WHERE is_active")
                    context_count = cur.fetchone()["n"]
                    cur.execute("SELECT COUNT(*) AS n FROM brain_soul_syntheses")
                    synthesis_count = cur.fetchone()["n"]
                    cur.execute(
                        "SELECT created_at FROM brain_soul_syntheses ORDER BY created_at DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    if row:
                        latest_synthesis = row["created_at"].isoformat()
    except Exception:
        pass

    return {
        "tables_ready": tables_ready,
        "active_context_entries": context_count,
        "total_syntheses": synthesis_count,
        "latest_synthesis_at": latest_synthesis,
        "database_connected": store.database is not None,
    }
