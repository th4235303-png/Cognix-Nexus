from __future__ import annotations

import hmac
import logging
import os
from html import escape as html_escape
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from ..services.telegram import send_telegram_message
from ..store import store, now_iso

logger = logging.getLogger("cognix.telegram")

router = APIRouter(prefix="/telegram", tags=["telegram"])

FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "https://cognix-nexus-frontend.onrender.com")


def _production_mode() -> bool:
    return os.getenv("COGNIX_ENV", "development").strip().lower() in {"production", "prod"}


def _configured_id_set(name: str) -> set[str]:
    return {part.strip() for part in os.getenv(name, "").split(",") if part.strip()}


def _is_allowed_telegram_chat(chat_id: int | str | None) -> bool:
    """Limit bot interactions to the configured group, failing closed in production."""
    allowed_chat = os.getenv("TELEGRAM_ALLOWED_CHAT_ID", "").strip() or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if _production_mode() and not allowed_chat:
        return False
    return not allowed_chat or str(chat_id).strip() == allowed_chat


def _is_allowed_telegram_context(*, user_id: int | str | None, chat_id: int | str | None, topic_id: int | None) -> bool:
    """Authorize an inbound Telegram actor against user, group, and topic scope."""
    allowed_users = _configured_id_set("TELEGRAM_ALLOWED_USER_IDS")
    expected_topic = os.getenv("TELEGRAM_ALLOWED_TOPIC_ID", "").strip() or os.getenv("TELEGRAM_TOPIC_ID", "").strip()

    if _production_mode() and (not allowed_users or not expected_topic):
        logger.error("Telegram authorization is not fully configured")
        return False
    if allowed_users and str(user_id).strip() not in allowed_users:
        return False
    if expected_topic and (topic_id is None or str(topic_id) != expected_topic):
        return False
    return _is_allowed_telegram_chat(chat_id)


def _authorize_action_gateway(secret: str | None) -> None:
    expected_secret = os.getenv("TELEGRAM_ACTION_SECRET", "").strip()
    if not expected_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram action gateway is not configured")
    if not secret or not hmac.compare_digest(secret, expected_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram action credentials")


class TelegramActionPayload(BaseModel):
    action: str
    chat_id: int | str | None = None
    topic_id: int | None = None
    user_id: int | None = None
    username: str | None = None
    raw_message: str | None = None


# ------------------------------------------------------------------------------
# 1. ACTION HANDLER (Direct Callback / Gateway)
# ------------------------------------------------------------------------------
@router.post("/action")
async def handle_telegram_action(
    payload: TelegramActionPayload,
    x_telegram_action_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    """Handle a gateway action only after shared-secret and scope checks."""
    _authorize_action_gateway(x_telegram_action_secret)
    if not _is_allowed_telegram_context(user_id=payload.user_id, chat_id=payload.chat_id, topic_id=payload.topic_id):
        logger.warning("Ignored Telegram action outside the authorized user/group/topic scope")
        return {"status": "ignored", "reason": "chat_not_allowed"}

    return await _execute_telegram_action(payload)


async def _execute_telegram_action(payload: TelegramActionPayload) -> dict[str, Any]:
    """Execute an action after its caller has already been authorized."""

    action = payload.action
    logger.info("Cognix received Telegram action: %s", action)

    # 1. Flashcard Reveal
    if action.startswith("cognix_reveal:"):
        card_id = action.split(":", 1)[1]
        msg = f"💡 <b>Flashcard Answer ({card_id}):</b>\nKnowledge retrieval is reinforced via active recall and spaced repetition."
        await send_telegram_message(msg, topic_id=payload.topic_id, chat_id=payload.chat_id)
        return {"status": "ok", "action": "flashcard_revealed", "id": card_id}

    # 2. Flashcard Grade (Spaced Repetition adjustment)
    elif action.startswith("cognix_grade_easy:") or action.startswith("cognix_grade_hard:"):
        # Avoid claiming a schedule update until a durable flashcard scheduler exists.
        card_id = action.split(":", 1)[1]
        await send_telegram_message(
            "⚠️ Flashcard grading is not persisted yet; no review schedule was changed.",
            topic_id=payload.topic_id,
            chat_id=payload.chat_id,
        )
        return {"status": "not_implemented", "action": action.split(":", 1)[0], "id": card_id}

    # 3. Quick Note/Link Capture to the configured owner's durable Brain Vault
    elif action == "cognix_quick_capture" and payload.raw_message:
        note_text = payload.raw_message.strip()
        owner_id = os.getenv("COGNIX_TELEGRAM_OWNER_ID", "").strip()
        if not owner_id or store.database is None:
            await send_telegram_message(
                "⚠️ Capture is unavailable: configure COGNIX_TELEGRAM_OWNER_ID and a durable PostgreSQL database.",
                topic_id=payload.topic_id,
                chat_id=payload.chat_id,
            )
            return {"status": "unavailable", "action": "quick_capture"}
        if not note_text:
            return {"status": "ignored", "action": "quick_capture", "reason": "empty_content"}
        note_id = f"NOTE-{uuid4().hex[:8].upper()}"
        now = now_iso()
        note = {
            "id": note_id,
            "title": note_text[:120] or "Telegram capture",
            "content": note_text,
            "note_type": "telegram_capture",
            "status": "inbox",
            "created_at": now,
            "updated_at": now,
        }
        store.save_brain_note(note, owner_id)
        store.brain_notes[note_id] = note
        store.brain_note_owners[note_id] = owner_id
        store.add_activity("brain_note_created", note_id, "new", "inbox")
        safe_preview = html_escape(note_text[:120])
        await send_telegram_message(
            f"🧠 <b>Saved to Brain Vault Inbox</b> (ID: <code>{note_id}</code>)\n<i>{safe_preview}</i>",
            topic_id=payload.topic_id,
            chat_id=payload.chat_id,
        )
        return {"status": "ok", "action": "quick_captured", "id": note_id}

    return {"status": "ignored", "action": action}


# ------------------------------------------------------------------------------
# 2. AI MORNING DIGEST GENERATOR
# ------------------------------------------------------------------------------
async def send_cognix_morning_digest(
    topic_id: int | None = None,
    chat_id: int | str | None = None,
) -> dict[str, Any] | None:
    """Send a static learning prompt; it does not query live vault or review data."""
    msg = (
        "☀️ <b>[Cognix-Nexus] AI Morning Knowledge Digest</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🧠 <b>Brain Vault:</b> Retrieval health is not checked by this digest\n"
        "📚 <b>Spaced Repetition:</b> Live review count is not connected yet\n"
        "💡 <b>Today's Core Principle:</b>\n"
        "<i>\"Understanding is a compression algorithm. If you cannot explain it concisely, your representation is unoptimized.\"</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Tap below to open your Second Brain:</i>"
    )
    keyboard = [
        [
            {"text": "🧠 Open Brain Vault (Mini App)", "url": FRONTEND_URL},
        ],
        [
            {"text": "💡 Review Flashcards", "callback_data": "cognix_reveal:daily_deck"},
            {"text": "📥 Capture Idea", "callback_data": "cognix_quick_capture"},
        ]
    ]
    return await send_telegram_message(msg, topic_id=topic_id, chat_id=chat_id, inline_keyboard=keyboard)


# ------------------------------------------------------------------------------
# 3. NATIVE TELEGRAM WEBHOOK & SLASH COMMANDS ROUTER
# ------------------------------------------------------------------------------
@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, Any]:
    """Native Telegram Webhook handler for Cognix Nexus."""
    expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    provided_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "").strip()
    if not expected_secret:
        raise HTTPException(status_code=503, detail="Telegram webhook is not configured")
    if not provided_secret or not hmac.compare_digest(provided_secret, expected_secret):
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")
    try:
        update = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON"}

    # Callback Query (Buttons)
    if "callback_query" in update:
        cq = update["callback_query"]
        action = cq.get("data", "")
        message = cq.get("message", {})
        topic_id = message.get("message_thread_id")
        payload = TelegramActionPayload(
            action=action,
            chat_id=message.get("chat", {}).get("id"),
            topic_id=topic_id,
            user_id=cq.get("from", {}).get("id"),
            username=cq.get("from", {}).get("username"),
        )
        if not _is_allowed_telegram_context(user_id=payload.user_id, chat_id=payload.chat_id, topic_id=payload.topic_id):
            return {"ok": True, "ignored": "unauthorized_scope"}
        return await _execute_telegram_action(payload)

    # Message Text (Slash Commands)
    if "message" in update:
        msg = update["message"]
        text = msg.get("text", "").strip()
        topic_id = msg.get("message_thread_id")
        chat_id = msg.get("chat", {}).get("id")

        user_id = msg.get("from", {}).get("id")
        if not _is_allowed_telegram_context(user_id=user_id, chat_id=chat_id, topic_id=topic_id):
            logger.warning("Ignored Telegram message outside the authorized user/group/topic scope")
            return {"ok": True, "ignored": "unauthorized_scope"}

        if not text:
            return {"ok": True}

        # Command: /start or /help
        if text.startswith("/start") or text.startswith("/help"):
            help_text = (
                "🧠 <b>Cognix-Nexus Second Brain Commands:</b>\n\n"
                "• <code>/status</code> — Check database reachability and Telegram configuration\n"
                "• <code>/morning_brief</code> — Today's learning flashcards & digest\n"
                "• <code>/ask [question]</code> — Find matching Brain Vault notes (keyword search)\n"
                "• <code>/capture [thought]</code> — Save a thought to the configured Brain Vault owner\n\n"
                "👇 Click below to open Brain Vault inside Telegram:"
            )
            buttons = [
                [{"text": "🧠 Open Brain Vault", "url": FRONTEND_URL}]
            ]
            await send_telegram_message(help_text, topic_id=topic_id, chat_id=chat_id, inline_keyboard=buttons)
            return {"ok": True, "command": "help"}

        # Command: /status
        elif text.startswith("/status"):
            db_status = "not configured"
            if store.database is not None:
                try:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT 1")
                            cur.fetchone()
                    db_status = "reachable"
                except Exception:
                    logger.exception("Telegram /status database health check failed")
                    db_status = "unreachable"
            telegram_status = "enabled by configuration" if os.getenv("TELEGRAM_ENABLED", "false").strip().lower() == "true" else "disabled by configuration"
            status_text = (
                "🩺 <b>[Cognix-Nexus] Runtime Status</b>\n\n"
                f"• <b>Database:</b> <code>{db_status}</code>\n"
                f"• <b>Telegram delivery:</b> <code>{telegram_status}</code>\n"
                "• <b>Vector search / queues / Drive:</b> <code>not checked by this command</code>"
            )
            buttons = [
                [{"text": "🧠 Open Brain Vault", "url": FRONTEND_URL}]
            ]
            await send_telegram_message(status_text, topic_id=topic_id, chat_id=chat_id, inline_keyboard=buttons)
            return {"ok": True, "command": "status"}

        # Command: /morning_brief
        elif text.startswith("/morning_brief") or text.startswith("/digest"):
            await send_cognix_morning_digest(topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "morning_brief"}

        # Command: /ask <query>
        elif text.startswith("/ask"):
            query = text[len("/ask"):].strip()
            if not query:
                await send_telegram_message("⚠️ Please supply a query: <code>/ask [question]</code>", topic_id=topic_id, chat_id=chat_id)
                return {"ok": True}
            
            owner_id = os.getenv("COGNIX_TELEGRAM_OWNER_ID", "").strip()
            if not owner_id or store.database is None:
                await send_telegram_message(
                    "⚠️ Retrieval is unavailable: configure COGNIX_TELEGRAM_OWNER_ID and PostgreSQL.",
                    topic_id=topic_id,
                    chat_id=chat_id,
                )
                return {"ok": True, "command": "ask", "status": "unavailable"}
            terms = [term for term in query.lower().split() if len(term) > 1]
            notes = store.list_brain_notes_for_owner(owner_id)
            ranked = []
            for note in notes:
                content = str(note.get("content", ""))
                score = sum(content.lower().count(term) for term in terms)
                if score:
                    ranked.append((score, note))
            ranked.sort(key=lambda item: item[0], reverse=True)
            if ranked:
                lines = ["🔎 <b>Matching Brain Vault notes</b>", ""]
                for score, note in ranked[:3]:
                    title = html_escape(str(note.get("title", "Untitled"))[:100])
                    snippet = html_escape(str(note.get("content", ""))[:500])
                    lines.append(f"• <b>{title}</b> (match: {score})\n{snippet}")
                reply = "\n\n".join(lines)
            else:
                reply = "🔎 No matching notes were found in the Brain Vault. This command performs keyword matching, not AI synthesis."
            await send_telegram_message(reply, topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "ask", "matches": len(ranked), "mode": "keyword"}

        # Command: /capture <note>
        elif text.startswith("/capture"):
            content = text[len("/capture"):].strip()
            if not content:
                await send_telegram_message("⚠️ Please provide content: <code>/capture [your idea or link]</code>", topic_id=topic_id, chat_id=chat_id)
                return {"ok": True}
            payload = TelegramActionPayload(action="cognix_quick_capture", raw_message=content, topic_id=topic_id, chat_id=chat_id, user_id=user_id)
            return await _execute_telegram_action(payload)

        # Command: /brain - Brain vault statistics
        elif text.startswith("/brain"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT COUNT(*) AS cnt FROM sources")
                            src_count = cur.fetchone()["cnt"]
                            cur.execute("SELECT COUNT(*) AS cnt FROM processing_tasks")
                            task_count = cur.fetchone()["cnt"]
                            cur.execute("SELECT COUNT(*) AS cnt FROM claims")
                            claim_count = cur.fetchone()["cnt"]
                    reply = (
                        "\U0001f9e0 <b>[Cognix] Brain Vault Stats</b>\n\n"
                        f"\U0001f4da Sources: <code>{src_count}</code>\n"
                        f"\u2699\ufe0f Tasks: <code>{task_count}</code>\n"
                        f"\U0001f4dd Claims: <code>{claim_count}</code>"
                    )
                else:
                    reply = "\u26a0\ufe0f Database not connected."
                await send_telegram_message(reply, topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /brain failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch brain stats.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "brain"}

        # Command: /sources - list recent sources
        elif text.startswith("/sources"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, title, source_type FROM sources ORDER BY created_at DESC LIMIT 5")
                            rows = cur.fetchall()
                    lines = ["\U0001f4da <b>[Cognix] Recent Sources</b>\n"]
                    for r in (rows or []):
                        title = html_escape(str(r.get("title", "?"))[:45])
                        lines.append(f"  \u2022 <code>{title}</code> [{r.get('source_type', '?')}]")
                    if not rows:
                        lines.append("<i>No sources yet.</i>")
                    await send_telegram_message("\n".join(lines), topic_id=topic_id, chat_id=chat_id)
                else:
                    await send_telegram_message("\u26a0\ufe0f Database not connected.", topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /sources failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch sources.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "sources"}

        # Command: /reviews - pending reviews
        elif text.startswith("/review"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT COUNT(*) AS cnt FROM reviews")
                            total = cur.fetchone()["cnt"]
                            cur.execute("SELECT COUNT(*) AS cnt FROM reviews WHERE status = 'pending'")
                            pending = cur.fetchone()["cnt"]
                    reply = f"\U0001f50d <b>[Cognix] Reviews</b>\n\nTotal: <code>{total}</code>\nPending: <code>{pending}</code>"
                    await send_telegram_message(reply, topic_id=topic_id, chat_id=chat_id)
                else:
                    await send_telegram_message("\u26a0\ufe0f Database not connected.", topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /reviews failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch reviews.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "reviews"}

        # Command: /tasks - processing task breakdown
        elif text.startswith("/tasks"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT status, COUNT(*) AS cnt FROM processing_tasks GROUP BY status ORDER BY cnt DESC")
                            rows = cur.fetchall()
                    lines = ["\u2699\ufe0f <b>[Cognix] Processing Tasks</b>\n"]
                    for r in (rows or []):
                        lines.append(f"  \u2022 {r['status']}: <code>{r['cnt']}</code>")
                    if not rows:
                        lines.append("<i>No tasks found.</i>")
                    await send_telegram_message("\n".join(lines), topic_id=topic_id, chat_id=chat_id)
                else:
                    await send_telegram_message("\u26a0\ufe0f Database not connected.", topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /tasks failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch tasks.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "tasks"}

        # Command: /exports - recent export jobs
        elif text.startswith("/export"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, status, created_at FROM export_jobs ORDER BY created_at DESC LIMIT 5")
                            rows = cur.fetchall()
                    lines = ["\U0001f4e6 <b>[Cognix] Recent Exports</b>\n"]
                    for r in (rows or []):
                        st_icon = "\u2705" if r.get("status") == "completed" else "\u23f3"
                        eid = str(r["id"])[:8]
                        lines.append(f"  {st_icon} {eid}... [{r.get('status', '?')}]")
                    if not rows:
                        lines.append("<i>No exports found.</i>")
                    await send_telegram_message("\n".join(lines), topic_id=topic_id, chat_id=chat_id)
                else:
                    await send_telegram_message("\u26a0\ufe0f Database not connected.", topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /exports failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch exports.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "exports"}

        # Command: /activity - recent events
        elif text.startswith("/activity"):
            try:
                if store.database:
                    with store.database.connect() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT event_type, created_at FROM activity_events ORDER BY created_at DESC LIMIT 5")
                            rows = cur.fetchall()
                    lines = ["\U0001f4c5 <b>[Cognix] Recent Activity</b>\n"]
                    for r in (rows or []):
                        ts = str(r.get("created_at", ""))[:16]
                        lines.append(f"  \u2022 [{ts}] {r.get('event_type', '?')}")
                    if not rows:
                        lines.append("<i>No recent activity.</i>")
                    await send_telegram_message("\n".join(lines), topic_id=topic_id, chat_id=chat_id)
                else:
                    await send_telegram_message("\u26a0\ufe0f Database not connected.", topic_id=topic_id, chat_id=chat_id)
            except Exception:
                logger.exception("Telegram /activity failed")
                await send_telegram_message("\u26a0\ufe0f Could not fetch activity.", topic_id=topic_id, chat_id=chat_id)
            return {"ok": True, "command": "activity"}

    return {"ok": True}
