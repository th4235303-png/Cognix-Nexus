import unittest
from unittest.mock import patch

from app.services.book_processing import process_queued_books


class _Cursor:
    def __init__(self):
        self.query = ""
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchall(self):
        return []


class _Connection:
    def __init__(self, cursor):
        self.cursor_instance = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self.cursor_instance


class _Database:
    def __init__(self):
        self.query_cursor = _Cursor()

    def connect(self):
        return _Connection(self.query_cursor)


class BookProcessingQueueContractTests(unittest.TestCase):
    def test_queue_does_not_select_filename_only_rows_without_binary_reference(self):
        database = _Database()
        with patch("app.services.book_processing.store") as store_mock:
            store_mock.database = database
            self.assertEqual(process_queued_books(limit=2), 0)

        query = " ".join(database.query_cursor.query.split()).lower()
        self.assertIn("binary_path is not null or binary_storage is not null", query)
        self.assertNotIn("original_filename is not null", query)
        self.assertEqual(database.query_cursor.params, (2,))


if __name__ == "__main__":
    unittest.main()
