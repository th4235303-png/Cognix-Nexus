from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from app.routers.level_up import (
    FlashcardCreate,
    FlashcardGrade,
    create_flashcard_review,
    grade_flashcard_review,
    list_flashcard_reviews,
)


class FlashcardReviewPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = MagicMock()
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.database.connect.return_value.__enter__.return_value = self.connection
        self.connection.cursor.return_value.__enter__.return_value = self.cursor
        self.connection.__enter__.return_value = self.connection

    def test_create_persists_owner_and_card_content(self) -> None:
        self.cursor.fetchone.return_value = {"id": "LREV-test", "owner_id": "owner-1"}
        with patch("app.routers.level_up._db", return_value=self.database), patch(
            "app.routers.level_up.owner_for_request", return_value="owner-1"
        ):
            result = create_flashcard_review(
                FlashcardCreate(subject="Personal note", question="Q?", answer="A", source_id="note-1"),
                request=None,  # type: ignore[arg-type]
            )
        self.assertEqual(result["owner_id"], "owner-1")
        query, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO learning_reviews(id,owner_id", query)
        self.assertEqual(params[1], "owner-1")
        metadata = json.loads(params[-1])
        self.assertEqual(metadata["question"], "Q?")
        self.assertEqual(metadata["answer"], "A")
        self.connection.commit.assert_called_once()

    def test_list_reviews_is_owner_scoped(self) -> None:
        self.cursor.fetchall.return_value = [{"id": "LREV-test"}]
        with patch("app.routers.level_up._db", return_value=self.database), patch(
            "app.routers.level_up.owner_for_request", return_value="owner-2"
        ):
            result = list_flashcard_reviews(request=None, due_only=True, limit=200)  # type: ignore[arg-type]
        self.assertEqual(result["total"], 1)
        query, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE owner_id=%s", query)
        self.assertIn("due_at <= now()", query)
        self.assertEqual(params, ("owner-2", 100))

    def test_grade_persists_sm2_interval_and_owner_filter(self) -> None:
        self.cursor.fetchone.side_effect = [
            {"id": "LREV-test", "metadata": {"question": "Q?", "answer": "A", "repetition": 1, "interval_days": 1, "ease_factor": 2.5}},
            {"id": "LREV-test", "rating": 4, "metadata": {"repetition": 2, "interval_days": 6, "ease_factor": 2.5}},
        ]
        with patch("app.routers.level_up._db", return_value=self.database), patch(
            "app.routers.level_up.owner_for_request", return_value="owner-3"
        ):
            result = grade_flashcard_review("LREV-test", FlashcardGrade(quality=4), request=None)  # type: ignore[arg-type]
        self.assertEqual(result["rating"], 4)
        self.assertEqual(self.cursor.execute.call_count, 2)
        update_query, update_params = self.cursor.execute.call_args.args
        self.assertIn("WHERE id=%s AND owner_id=%s RETURNING *", update_query)
        self.assertEqual(update_params[-2:], ("LREV-test", "owner-3"))
        metadata = json.loads(update_params[2])
        self.assertEqual(metadata["interval_days"], 6)
        self.assertEqual(metadata["last_quality"], 4)
        self.connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
