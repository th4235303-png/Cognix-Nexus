from __future__ import annotations

import logging
import os
from typing import Any
import httpx

logger = logging.getLogger("cognix.telegram")

TELEGRAM_API_BASE = "https://api.telegram.org"


def _get_config() -> tuple[str, str, int | None, bool]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    topic_str = os.getenv("TELEGRAM_TOPIC_ID", "").strip()
    topic_id = int(topic_str) if topic_str.isdigit() else None
    enabled = os.getenv("TELEGRAM_ENABLED", "false").strip().lower() == "true"
    return token, chat_id, topic_id, enabled


async def send_telegram_message(
    text: str,
    *,
    topic_id: int | None = None,
    parse_mode: str = "HTML",
    inline_keyboard: list[list[dict[str, str]]] | None = None,
    disable_web_page_preview: bool = False,
) -> dict[str, Any] | None:
    """Send an asynchronous message to Telegram group/topic for Cognix Nexus."""
    token, chat_id, default_topic, enabled = _get_config()
    effective_topic = topic_id if topic_id is not None else default_topic

    if not token or not chat_id:
        logger.info("[Telegram:Cognix:DryRun] %s", text.replace("\n", " "))
        return None

    if not enabled:
        logger.debug("[Telegram:Cognix:Disabled] %s", text.replace("\n", " "))
        return None

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }

    if effective_topic:
        payload["message_thread_id"] = int(effective_topic)

    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error("Telegram API error (%s): %s", response.status_code, response.text)
                return None
            return response.json()
    except Exception as exc:
        logger.warning("Failed to send Telegram message from Cognix: %s", exc)
        return None


async def send_notification(
    title: str,
    details: str,
    *,
    status: str = "INFO",
    topic_id: int | None = None,
    actions: list[tuple[str, str]] | None = None,
) -> dict[str, Any] | None:
    """Send standardized Cognix Brain Vault notification."""
    icon_map = {
        "SUCCESS": "✨",
        "INFO": "🧠",
        "WARNING": "⚠️",
        "ERROR": "🚨",
    }
    status_icon = icon_map.get(status.upper(), "🧠")

    lines = [
        f"🧠 <b>[Cognix-Nexus]</b> {status_icon} <b>{title}</b>",
        "",
        details,
    ]
    text = "\n".join(lines)

    inline_keyboard = None
    if actions:
        row: list[dict[str, str]] = []
        for label, callback_or_url in actions:
            if callback_or_url.startswith("http://") or callback_or_url.startswith("https://"):
                row.append({"text": label, "url": callback_or_url})
            else:
                row.append({"text": label, "callback_data": callback_or_url})
        inline_keyboard = [row]

    return await send_telegram_message(text, topic_id=topic_id, inline_keyboard=inline_keyboard)


# ==========================================
# Cognix Domain Hooks
# ==========================================

async def notify_book_distilled(book_title: str, insights_count: int, summary_snippet: str = "") -> None:
    """Notify when AI Reading Room completes book distillation."""
    details = f"📚 <b>Book:</b> <i>{book_title}</i>\n💡 <b>Distilled Insights:</b> {insights_count} concepts"
    if summary_snippet:
        short = (summary_snippet[:150] + "...") if len(summary_snippet) > 150 else summary_snippet
        details += f"\n\n📝 <i>\"{short}\"</i>"

    actions = [
        ("🧠 View in Brain Vault", f"cognix_vault_book:{book_title}"),
    ]
    await send_notification("Book Distillation Complete", details, status="SUCCESS", actions=actions)


async def notify_research_ingested(source_title: str, claims_count: int) -> None:
    """Notify when new research paper/article is ingested."""
    details = f"🔬 <b>Source:</b> {source_title}\n📊 <b>Claims Extracted:</b> {claims_count} verifiable claims"
    await send_notification("Research Ingested", details, status="INFO")


async def notify_daily_flashcard(card_id: str, concept: str, question: str) -> None:
    """Send daily spaced-repetition knowledge card."""
    details = f"🎯 <b>Daily Concept:</b> <b>{concept}</b>\n\n❓ <b>Question:</b>\n{question}"
    actions = [
        ("💡 Reveal Answer", f"cognix_reveal:{card_id}"),
        ("✅ I Knew This", f"cognix_grade_easy:{card_id}"),
        ("❌ Review Again", f"cognix_grade_hard:{card_id}"),
    ]
    await send_notification("Spaced Repetition Review", details, status="INFO", actions=actions)


async def notify_vault_sync(items_count: int) -> None:
    """Notify when Brain Vault synchronizes with external drives/notes."""
    details = f"🔄 <b>Synchronized:</b> {items_count} notes & knowledge graph nodes."
    await send_notification("Vault Sync Complete", details, status="SUCCESS")
