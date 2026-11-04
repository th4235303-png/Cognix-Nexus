import os
import unittest
from unittest.mock import patch

from app.services import telegram


class _Response:
    status_code = 200

    @staticmethod
    def json():
        return {"ok": True, "result": {"message_id": 1}}


class _AsyncClient:
    payload = None
    url = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        type(self).url = url
        type(self).payload = json
        return _Response()


class TelegramChatRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_reply_uses_originating_chat_without_static_chat_id(self):
        _AsyncClient.payload = None
        _AsyncClient.url = None
        env = {
            "TELEGRAM_BOT_TOKEN": "test-bot-token",
            "TELEGRAM_CHAT_ID": "",
            "TELEGRAM_TOPIC_ID": "",
            "TELEGRAM_ENABLED": "true",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            telegram.httpx, "AsyncClient", _AsyncClient
        ):
            result = await telegram.send_telegram_message(
                "hello from Cognix",
                chat_id=123456,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(_AsyncClient.payload["chat_id"], "123456")
        self.assertTrue(_AsyncClient.url.endswith("/bottest-bot-token/sendMessage"))

    async def test_configured_chat_remains_default_for_notifications(self):
        _AsyncClient.payload = None
        env = {
            "TELEGRAM_BOT_TOKEN": "test-bot-token",
            "TELEGRAM_CHAT_ID": "-1001234567890",
            "TELEGRAM_TOPIC_ID": "",
            "TELEGRAM_ENABLED": "true",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            telegram.httpx, "AsyncClient", _AsyncClient
        ):
            await telegram.send_telegram_message("notification")

        self.assertEqual(_AsyncClient.payload["chat_id"], "-1001234567890")

    async def test_morning_digest_uses_url_buttons_compatible_with_group_chats(self):
        _AsyncClient.payload = None
        env = {
            "TELEGRAM_BOT_TOKEN": "test-bot-token",
            "TELEGRAM_CHAT_ID": "",
            "TELEGRAM_TOPIC_ID": "",
            "TELEGRAM_ENABLED": "true",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            telegram.httpx, "AsyncClient", _AsyncClient
        ):
            from app.routers.telegram import send_cognix_morning_digest
            await send_cognix_morning_digest(chat_id=123456)

        keyboard = _AsyncClient.payload["reply_markup"]["inline_keyboard"]
        self.assertEqual(keyboard[0][0]["url"], "https://cognix-nexus-frontend.onrender.com")
        self.assertNotIn("web_app", keyboard[0][0])


if __name__ == "__main__":
    unittest.main()
