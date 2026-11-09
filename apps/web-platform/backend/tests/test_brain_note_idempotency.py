from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import Request

from app.routers.brain_vault import NoteCreate, create_note


def make_request(idempotency_key: str) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/brain/notes",
        "headers": [(b"idempotency-key", idempotency_key.encode())],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("test-client", 123),
        "scheme": "http",
    })


class BrainNoteIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = MagicMock()
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.database.connect.return_value.__enter__.return_value = self.connection
        self.connection.cursor.return_value.__enter__.return_value = self.cursor

    def test_first_request_inserts_idempotency_key(self) -> None:
        self.cursor.fetchone.return_value = {"id": "NOTE-new"}
        with patch("app.routers.brain_vault.store.database", self.database), patch(
            "app.routers.brain_vault.owner_for_request", return_value="owner-1"
        ), patch("app.routers.brain_vault.store.add_activity") as activity:
            result = create_note(
                NoteCreate(title="Capture", content="persist this", note_type="#idea", status="inbox"),
                make_request("mobile-capture-1"),
            )
        self.assertEqual(result["idempotency_key"], "mobile-capture-1")
        query, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO notes", query)
        self.assertIn("idempotency_key", query)
        self.assertEqual(params[-1], "mobile-capture-1")
        self.connection.commit.assert_called_once()
        activity.assert_called_once()

    def test_retry_returns_existing_note_without_duplicate_activity(self) -> None:
        self.cursor.fetchone.side_effect = [None, {"id": "NOTE-existing"}]
        existing_note = {"id": "NOTE-existing", "content": "persist this"}
        self.database.get_brain_note_for_owner.return_value = existing_note
        with patch("app.routers.brain_vault.store.database", self.database), patch(
            "app.routers.brain_vault.owner_for_request", return_value="owner-1"
        ), patch("app.routers.brain_vault.store.add_activity") as activity:
            result = create_note(
                NoteCreate(title="Capture", content="persist this", note_type="#idea", status="inbox"),
                make_request("mobile-capture-1"),
            )
        self.assertEqual(result, existing_note)
        self.assertEqual(self.cursor.execute.call_count, 2)
        select_query, select_params = self.cursor.execute.call_args.args
        self.assertIn("SELECT id FROM notes", select_query)
        self.assertEqual(select_params, ("owner-1", "mobile-capture-1"))
        activity.assert_not_called()


if __name__ == "__main__":
    unittest.main()
