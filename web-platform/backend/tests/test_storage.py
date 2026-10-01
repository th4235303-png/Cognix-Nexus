import os
import unittest
from unittest.mock import patch

from app.services.book_storage import BookBinaryStorage
from app.services.object_storage import B2ObjectStorage, R2ObjectStorage, SupabaseObjectStorage, S3ObjectStorage
from app.main import app
from fastapi.testclient import TestClient


class StorageContractTests(unittest.TestCase):
    def test_local_storage_requires_explicit_directory(self):
        with patch.dict(os.environ, {"COGNIX_BOOK_STORAGE_PROVIDER": "local", "COGNIX_BOOK_STORAGE_DIR": ""}, clear=False):
            self.assertFalse(BookBinaryStorage().configured)

    def test_b2_requires_all_credentials(self):
        with patch.dict(
            os.environ,
            {
                "COGNIX_B2_ENDPOINT": "https://s3.us-east-005.backblazeb2.com",
                "COGNIX_B2_BUCKET": "cognix",
                "COGNIX_B2_KEY_ID": "",
                "COGNIX_B2_APPLICATION_KEY": "",
            },
            clear=False,
        ):
            self.assertFalse(B2ObjectStorage().configured)

    def test_r2_requires_all_credentials(self):
        with patch.dict(
            os.environ,
            {
                "COGNIX_R2_ENDPOINT": "https://example.r2.cloudflarestorage.com",
                "COGNIX_R2_BUCKET": "cognix",
                "COGNIX_R2_ACCESS_KEY_ID": "",
                "COGNIX_R2_SECRET_ACCESS_KEY": "",
            },
            clear=False,
        ):
            self.assertFalse(R2ObjectStorage().configured)

    def test_supabase_storage_requires_backend_credentials(self):
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "",
                "COGNIX_SUPABASE_STORAGE_BUCKET": "cognix-artifacts",
            },
            clear=False,
        ):
            self.assertFalse(SupabaseObjectStorage().configured)

    def test_object_key_rejects_traversal_and_control_chars(self):
        for key in ("../secret", "books/../secret", "books\\secret", "books/\x00secret"):
            with self.assertRaises(ValueError):
                S3ObjectStorage._safe_key(key)

    def test_object_key_allows_nested_keys(self):
        self.assertEqual(S3ObjectStorage._safe_key("/books/BOOK-1/file.pdf"), "books/BOOK-1/file.pdf")

    def test_storage_status_never_returns_secret_values(self):
        client = TestClient(app)
        response = client.get("/integrations/storage/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("b2_configured", body)
        self.assertIn("supabase_storage_configured", body)
        self.assertNotIn("COGNIX_B2_APPLICATION_KEY", body)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", body)
        self.assertNotIn("GOOGLE_REFRESH_TOKEN", body)


if __name__ == "__main__":
    unittest.main()
