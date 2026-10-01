import os
import unittest
from unittest.mock import patch

from app.services.book_storage import BookBinaryStorage
from app.services.object_storage import R2ObjectStorage
from app.main import app
from fastapi.testclient import TestClient


class StorageContractTests(unittest.TestCase):
    def test_local_storage_requires_explicit_directory(self):
        with patch.dict(os.environ, {"COGNIX_BOOK_STORAGE_PROVIDER": "local"}, clear=False):
            with patch.dict(os.environ, {"COGNIX_BOOK_STORAGE_DIR": ""}, clear=False):
                self.assertFalse(BookBinaryStorage().configured)

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

    def test_storage_status_never_returns_secret_values(self):
        client = TestClient(app)
        response = client.get("/integrations/storage/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("r2_configured", body)
        self.assertNotIn("COGNIX_R2_SECRET_ACCESS_KEY", body)
        self.assertNotIn("GOOGLE_REFRESH_TOKEN", body)


if __name__ == "__main__":
    unittest.main()
