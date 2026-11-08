from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def configure_telegram_webhook() -> None:
    """Register the Telegram webhook URL and secret with the Bot API."""
    if os.getenv("TELEGRAM_ENABLED", "false").strip().lower() not in {"1", "true", "yes"}:
        logger.info("Telegram webhook setup skipped: Telegram integration is disabled")
        return

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    base_url = os.getenv("TELEGRAM_WEBHOOK_URL", "") or os.getenv("RENDER_EXTERNAL_URL", "")

    if not token:
        logger.warning("Telegram webhook setup skipped: bot token is not configured")
        return
    if not base_url:
        logger.warning("Telegram webhook setup skipped: TELEGRAM_WEBHOOK_URL and RENDER_EXTERNAL_URL are empty")
        return
    if len(secret) < 32:
        logger.warning("Telegram webhook setup skipped: TELEGRAM_WEBHOOK_SECRET must be at least 32 characters")
        return

    webhook_url = base_url if base_url.endswith("/telegram/webhook") else base_url.rstrip("/") + "/telegram/webhook"
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    payload = {
        "url": webhook_url,
        "secret_token": secret,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": False,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("ok") is True:
                logger.info("Telegram webhook configured successfully for Cognix Nexus")
            else:
                logger.error("Telegram webhook setup failed: Telegram API returned ok=false")
                return

            # Register bot commands for the group
            try:
                chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
                command_payload = {
                    "commands": [
                        {"command": "start", "description": "Connect to Cognix Nexus topic"},
                        {"command": "help", "description": "Show available commands"},
                        {"command": "status", "description": "Check Brain Vault & AI status"},
                        {"command": "morning_brief", "description": "Today's learning digest"},
                        {"command": "ask", "description": "Query your books & notes: /ask <question>"},
                        {"command": "capture", "description": "Save thought to Brain Vault: /capture <text>"},
                        {"command": "brain", "description": "View Brain Vault statistics"},
                        {"command": "sources", "description": "List recent knowledge sources"},
                        {"command": "review", "description": "Show items waiting for review"},
                        {"command": "tasks", "description": "Show processing tasks"},
                        {"command": "activity", "description": "Show recent Brain Vault activity"},
                    ],
                }
                if chat_id:
                    command_payload["scope"] = {"type": "chat", "chat_id": int(chat_id)}

                cmd_response = await client.post(
                    f"https://api.telegram.org/bot{token}/setMyCommands",
                    json=command_payload,
                )
                cmd_response.raise_for_status()
                cmd_result = cmd_response.json()
                if cmd_result.get("ok") is True:
                    logger.info("Telegram command menu configured for Cognix Nexus group")
                else:
                    logger.warning("Telegram command menu setup failed: API returned ok=false")
            except Exception as exc:
                logger.warning("Telegram command menu setup failed (%s)", type(exc).__name__)

            # Mirror BotFather's Menu Button setting in code so it survives
            # bot or deployment maintenance.  Telegram requires HTTPS Web App URLs.
            try:
                frontend_url = os.getenv("FRONTEND_BASE_URL", "https://cognix-nexus-frontend.onrender.com").strip()
                if frontend_url.startswith("https://"):
                    menu_response = await client.post(
                        f"https://api.telegram.org/bot{token}/setChatMenuButton",
                        json={
                            "menu_button": {
                                "type": "web_app",
                                "text": "Open Flow",
                                "web_app": {"url": frontend_url},
                            }
                        },
                    )
                    menu_response.raise_for_status()
                    logger.info("Telegram menu button configured for Cognix Nexus")
                else:
                    logger.warning("Telegram menu button skipped: FRONTEND_BASE_URL must use HTTPS")
            except Exception as exc:
                logger.warning("Telegram menu button setup failed (%s)", type(exc).__name__)

    except Exception as exc:
        logger.error("Telegram webhook setup failed (%s)", type(exc).__name__)
