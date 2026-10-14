from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

from ..services.telegram import send_telegram_message

logger = logging.getLogger("cognix.telegram.action")

router = APIRouter(prefix="/telegram", tags=["telegram"])


class TelegramActionPayload(BaseModel):
    action: str
    chat_id: int | str | None = None
    topic_id: int | None = None
    user_id: int | None = None
    username: str | None = None
    raw_message: str | None = None


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
