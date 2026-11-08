"""Fail-closed authorization tests for Cognix inbound Telegram actions."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.routers.telegram import _authorize_action_gateway, _is_allowed_telegram_context


class TelegramAuthorizationTests(unittest.TestCase):
    _secure_environment = {
        "COGNIX_ENV": "production",
        "TELEGRAM_ALLOWED_USER_IDS": "1686310706,6759217947",
        "TELEGRAM_CHAT_ID": "-1003992125718",
        "TELEGRAM_TOPIC_ID": "7",
    }

    def test_production_rejects_missing_allowlist(self):
        with patch.dict(os.environ, {"COGNIX_ENV": "production", "TELEGRAM_ALLOWED_USER_IDS": "", "TELEGRAM_CHAT_ID": "-1003992125718", "TELEGRAM_TOPIC_ID": "7"}, clear=False):
            self.assertFalse(_is_allowed_telegram_context(user_id=1686310706, chat_id=-1003992125718, topic_id=7))

    def test_allows_only_configured_user_chat_and_topic(self):
        with patch.dict(os.environ, self._secure_environment, clear=False):
            self.assertTrue(_is_allowed_telegram_context(user_id=1686310706, chat_id=-1003992125718, topic_id=7))
            self.assertTrue(_is_allowed_telegram_context(user_id=6759217947, chat_id=-1003992125718, topic_id=7))
            self.assertFalse(_is_allowed_telegram_context(user_id=999, chat_id=-1003992125718, topic_id=7))
            self.assertFalse(_is_allowed_telegram_context(user_id=1686310706, chat_id=-1003992125719, topic_id=7))
            self.assertFalse(_is_allowed_telegram_context(user_id=1686310706, chat_id=-1003992125718, topic_id=8))

    def test_direct_action_gateway_requires_its_own_secret(self):
        with patch.dict(os.environ, {"TELEGRAM_ACTION_SECRET": "gateway-secret"}, clear=False):
            with self.assertRaises(HTTPException) as invalid:
                _authorize_action_gateway("wrong-secret")
            self.assertEqual(invalid.exception.status_code, 401)
            _authorize_action_gateway("gateway-secret")

        with patch.dict(os.environ, {"TELEGRAM_ACTION_SECRET": ""}, clear=False):
            with self.assertRaises(HTTPException) as missing:
                _authorize_action_gateway("anything")
            self.assertEqual(missing.exception.status_code, 503)
