import os
import unittest
from unittest.mock import patch

from app.services.book_storage import BookBinaryStorage
from app.services.google_drive import _oauth_state, verify_oauth_state
from app.services.object_storage import B2ObjectStorage, CloudinaryObjectStorage, R2ObjectStorage, SupabaseObjectStorage, S3ObjectStorage
from app.main import app
from fastapi.testclient import TestClient


class StorageContractTests(unittest.TestCase):
    def test_local_storage_requires_explicit_directory(self):
        with patch.dict(os.environ, {"COGNIX_BOOK_STORAGE_PROVIDER": "local", "COGNIX_BOOK_STORAGE_DIR": ""}, clear=False):
            self.assertFalse(BookBinaryStorage().configured)

    def test_cloudinary_requires_all_credentials(self):
        with patch.dict(
            os.environ,
            {
                "CLOUDINARY_CLOUD_NAME": "demo",
                "CLOUDINARY_API_KEY": "key",
                "CLOUDINARY_API_SECRET": "",
            },
            clear=False,
        ):
            self.assertFalse(CloudinaryObjectStorage().configured)


    def test_cloudinary_book_storage_uses_provider_and_stored_key(self):
        class FakeCloudinary:
            configured = True
            def __init__(self):
                self.read_keys = []
                self.deleted_keys = []
            def get_bytes(self, key):
                self.read_keys.append(key)
                return b"pdf-bytes"
            def delete(self, key):
                self.deleted_keys.append(key)

        fake = FakeCloudinary()
        with patch.dict(os.environ, {"COGNIX_BOOK_STORAGE_PROVIDER": "cloudinary"}, clear=False), patch(
            "app.services.book_storage.cloudinary_storage", return_value=fake
        ):
            storage = BookBinaryStorage()
            self.assertTrue(storage.configured)
            self.assertEqual(storage.get("BOOK-1", "book.pdf", stored_key="cloudinary://asset-1"), b"pdf-bytes")
            storage.delete("BOOK-1", "book.pdf", stored_key="cloudinary://asset-1")
        self.assertEqual(fake.read_keys, ["cloudinary://asset-1"])
        self.assertEqual(fake.deleted_keys, ["cloudinary://asset-1"])

    def test_tiered_book_storage_routes_by_size(self):
        with patch.dict(
            os.environ,
            {
                "COGNIX_BOOK_STORAGE_PROVIDER": "tiered",
                "COGNIX_B2_LARGE_FILE_THRESHOLD_BYTES": "10",
            },
            clear=False,
        ):
            small = FakeStorage()
            large = FakeStorage()
            with patch("app.services.book_storage.supabase_storage", return_value=small), patch(
                "app.services.book_storage.b2_storage", return_value=large
            ):
                storage = BookBinaryStorage()
                self.assertEqual(storage.put("BOOK-1", "small.pdf", b"123").split("://", 1)[0], "supabase")
                self.assertEqual(storage.put("BOOK-2", "large.pdf", b"12345678901").split("://", 1)[0], "b2")

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

    def test_google_oauth_state_is_signed_and_time_bound(self):
        with patch.dict(os.environ, {"GOOGLE_CLIENT_SECRET": "test-secret"}, clear=False):
            state = _oauth_state()
            self.assertTrue(verify_oauth_state(state))
            self.assertFalse(verify_oauth_state(state + "x"))

    def test_storage_status_never_returns_secret_values(self):
        client = TestClient(app)
        response = client.get("/integrations/storage/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("cloudinary_configured", body)
        self.assertIn("b2_configured", body)
        self.assertIn("supabase_storage_configured", body)
        self.assertNotIn("COGNIX_B2_APPLICATION_KEY", body)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", body)
        self.assertNotIn("GOOGLE_REFRESH_TOKEN", body)


if __name__ == "__main__":
    unittest.main()
