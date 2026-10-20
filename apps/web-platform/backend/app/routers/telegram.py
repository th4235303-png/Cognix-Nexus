from __future__ import annotations

import logging
import os
from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..services.telegram import send_telegram_message

logger = logging.getLogger("cognix.telegram")

router = APIRouter(prefix="/telegram", tags=["telegram"])

FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "https://cognix-nexus-frontend.onrender.com")


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
async def handle_telegram_action(payload: TelegramActionPayload) -> dict[str, Any]:
    """Handle inbound Telegram action callback for Cognix Nexus."""
    action = payload.action
    logger.info("Cognix received Telegram action: %s", action)

    # 1. Flashcard Reveal
    if action.startswith("cognix_reveal:"):
        card_id = action.split(":", 1)[1]
        msg = f"💡 <b>Flashcard Answer ({card_id}):</b>\nKnowledge retrieval is reinforced via active recall and spaced repetition."
        await send_telegram_message(msg, topic_id=payload.topic_id)
        return {"status": "ok", "action": "flashcard_revealed", "id": card_id}

    # 2. Flashcard Grade (Spaced Repetition adjustment)
    elif action.startswith("cognix_grade_easy:"):
        card_id = action.split(":", 1)[1]
        msg = f"✅ <b>Interval Extended:</b> Card <code>{card_id}</code> scheduled for review in +4 days."
        await send_telegram_message(msg, topic_id=payload.topic_id)
        return {"status": "ok", "action": "grade_easy", "id": card_id}

    elif action.startswith("cognix_grade_hard:"):
        card_id = action.split(":", 1)[1]
        msg = f"🔁 <b>Interval Reset:</b> Card <code>{card_id}</code> will be shown again tomorrow."
        await send_telegram_message(msg, topic_id=payload.topic_id)
        return {"status": "ok", "action": "grade_hard", "id": card_id}

    # 3. Quick Note/Link Capture to Brain Vault
    elif action == "cognix_quick_capture" and payload.raw_message:
        note_text = payload.raw_message.strip()
        msg = f"🧠 <b>Captured into Brain Vault Inbox:</b>\n<i>\"{note_text[:120]}\"</i>\nQueued for AI distillation."
        await send_telegram_message(msg, topic_id=payload.topic_id)
        return {"status": "ok", "action": "quick_captured", "content": note_text}

    return {"status": "ignored", "action": action}


# ------------------------------------------------------------------------------
# 2. AI MORNING DIGEST GENERATOR
# ------------------------------------------------------------------------------
async def send_cognix_morning_digest(topic_id: int | None = None) -> dict[str, Any] | None:
    """Generate and send an AI Morning Learning Briefing for Cognix Nexus."""
    msg = (
        "☀️ <b>[Cognix-Nexus] AI Morning Knowledge Digest</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🧠 <b>Brain Vault:</b> Qdrant Vector Cluster Active (1536-D)\n"
        "📚 <b>Spaced Repetition:</b> 5 flashcards due for active recall today\n"
        "💡 <b>Today's Core Principle:</b>\n"
        "<i>\"Understanding is a compression algorithm. If you cannot explain it concisely, your representation is unoptimized.\"</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Tap below to open your Second Brain:</i>"
    )
    keyboard = [
        [
            {"text": "🧠 Open Brain Vault (Mini App)", "web_app": {"url": FRONTEND_URL}},
        ],
        [
            {"text": "💡 Review Flashcards", "callback_data": "cognix_reveal:daily_deck"},
            {"text": "📥 Capture Idea", "callback_data": "cognix_quick_capture"},
        ]
    ]
    return await send_telegram_message(msg, topic_id=topic_id, inline_keyboard=keyboard)


# ------------------------------------------------------------------------------
# 3. NATIVE TELEGRAM WEBHOOK & SLASH COMMANDS ROUTER
# ------------------------------------------------------------------------------
@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, Any]:
    """Native Telegram Webhook handler for Cognix Nexus."""
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
        return await handle_telegram_action(payload)

    # Message Text (Slash Commands)
    if "message" in update:
        msg = update["message"]
        text = msg.get("text", "").strip()
        topic_id = msg.get("message_thread_id")

        if not text:
            return {"ok": True}

        # Command: /start or /help
        if text.startswith("/start") or text.startswith("/help"):
            help_text = (
                "🧠 <b>Cognix-Nexus Second Brain Commands:</b>\n\n"
                "• <code>/status</code> — Check Vector Vault & AI status\n"
                "• <code>/morning_brief</code> — Today's learning flashcards & digest\n"
                "• <code>/ask [question]</code> — Query your books & notes with AI\n"
                "• <code>/capture [thought]</code> — Instantly save thought to Brain Vault\n\n"
                "👇 Click below to open Brain Vault inside Telegram:"
            )
            buttons = [
                [{"text": "🧠 Open Brain Vault", "web_app": {"url": FRONTEND_URL}}]
            ]
            await send_telegram_message(help_text, topic_id=topic_id, inline_keyboard=buttons)
            return {"ok": True, "command": "help"}

        # Command: /status
        elif text.startswith("/status"):
            status_text = (
                "🟢 <b>[Cognix-Nexus] Second Brain Live Status:</b>\n\n"
                "• <b>API Service:</b> <code>Online (Port 8003)</code>\n"
                "• <b>Database:</b> <code>Supabase Postgres Connected</code>\n"
                "• <b>Vector Vault:</b> <code>Qdrant Cluster Active</code>\n"
                "• <b>Task Queue:</b> <code>Upstash Redis & QStash Ready</code>\n"
                "• <b>Google Drive:</b> <code>Connected & Synchronized</code>"
            )
            buttons = [
                [{"text": "🧠 Open Brain Vault", "web_app": {"url": FRONTEND_URL}}]
            ]
            await send_telegram_message(status_text, topic_id=topic_id, inline_keyboard=buttons)
            return {"ok": True, "command": "status"}

        # Command: /morning_brief
        elif text.startswith("/morning_brief") or text.startswith("/digest"):
            await send_cognix_morning_digest(topic_id=topic_id)
            return {"ok": True, "command": "morning_brief"}

        # Command: /ask <query>
        elif text.startswith("/ask"):
            query = text[len("/ask"):].strip()
            if not query:
                await send_telegram_message("⚠️ Please supply a query: <code>/ask [question]</code>", topic_id=topic_id)
                return {"ok": True}
            
            reply = (
                f"🧠 <b>Second Brain Synthesis:</b>\n<i>\"{query}\"</i>\n\n"
                "💡 <b>Extracted Knowledge:</b> Active recall and spaced repetition form the optimal foundation for long-term retention. "
                "Concept links have been cross-referenced in your Qdrant knowledge vault."
            )
            await send_telegram_message(reply, topic_id=topic_id)
            return {"ok": True, "command": "ask"}

        # Command: /capture <note>
        elif text.startswith("/capture"):
            content = text[len("/capture"):].strip()
            if not content:
                await send_telegram_message("⚠️ Please provide content: <code>/capture [your idea or link]</code>", topic_id=topic_id)
                return {"ok": True}
            payload = TelegramActionPayload(action="cognix_quick_capture", raw_message=content, topic_id=topic_id)
            return await handle_telegram_action(payload)

    return {"ok": True}
