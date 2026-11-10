from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.routers.telegram import TelegramActionPayload, _execute_telegram_action
from app.store import store


class _FakeDatabase:
    def __init__(self) -> None:
        self.saved_notes: list[tuple[dict, str | None]] = []
        self.activity_events: list[dict] = []

    def save_brain_note(self, note: dict, owner_id: str | None) -> None:
        self.saved_notes.append((note.copy(), owner_id))

    def add_activity(self, event: dict) -> None:
        self.activity_events.append(event.copy())


class TelegramTruthfulActionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_capture_fails_closed_without_owner_or_database(self) -> None:
        with patch.dict("os.environ", {"COGNIX_TELEGRAM_OWNER_ID": ""}, clear=False), patch(
            "app.routers.telegram.send_telegram_message", new_callable=AsyncMock
        ):
            old_database = store.database
            try:
                store.database = None
                result = await _execute_telegram_action(
                    TelegramActionPayload(action="cognix_quick_capture", raw_message="test note")
                )
            finally:
                store.database = old_database
        self.assertEqual(result["status"], "unavailable")

    async def test_capture_persists_note_for_configured_owner(self) -> None:
        fake_database = _FakeDatabase()
        old_database = store.database
        with patch.dict("os.environ", {"COGNIX_TELEGRAM_OWNER_ID": "owner-test"}, clear=False), patch(
            "app.routers.telegram.send_telegram_message", new_callable=AsyncMock
        ):
            try:
                store.database = fake_database  # type: ignore[assignment]
                result = await _execute_telegram_action(
                    TelegramActionPayload(action="cognix_quick_capture", raw_message="durable note")
                )
            finally:
                store.database = old_database
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["action"], "quick_captured")
        self.assertEqual(len(fake_database.saved_notes), 1)
        note, owner_id = fake_database.saved_notes[0]
        self.assertEqual(owner_id, "owner-test")
        self.assertEqual(note["content"], "durable note")
        self.assertEqual(note["status"], "inbox")
        self.assertEqual(note["note_type"], "telegram_capture")
        self.assertEqual(len(fake_database.activity_events), 1)

    async def test_flashcard_grade_does_not_claim_schedule_update(self) -> None:
        with patch(
            "app.routers.telegram.send_telegram_message", new_callable=AsyncMock
        ) as send_message:
            result = await _execute_telegram_action(
                TelegramActionPayload(action="cognix_grade_easy:card-1")
            )
        self.assertEqual(result["status"], "not_implemented")
        send_message.assert_awaited_once()
        self.assertIn("not persisted", send_message.await_args.args[0])


if __name__ == "__main__":
    unittest.main()
