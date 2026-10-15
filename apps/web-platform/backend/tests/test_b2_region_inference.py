import os
import unittest
from unittest.mock import patch

from app.services.object_storage import B2ObjectStorage


class B2RegionInferenceTests(unittest.TestCase):
    def test_b2_endpoint_region_overrides_malformed_configured_region(self):
        env = {
            "COGNIX_B2_ENDPOINT": "https://s3.us-west-004.backblazeb2.com",
            "COGNIX_B2_BUCKET": "test-bucket",
            "COGNIX_B2_KEY_ID": "test-key",
            "COGNIX_B2_APPLICATION_KEY": "test-secret",
            "COGNIX_B2_REGION": "not a valid boto region",
        }
        with patch.dict(os.environ, env, clear=True):
            storage = B2ObjectStorage()

        self.assertEqual(storage.region, "us-west-004")
        self.assertTrue(storage.configured)

    def test_b2_keeps_default_region_when_endpoint_is_not_regional_b2(self):
        env = {
            "COGNIX_B2_ENDPOINT": "https://storage.example.test",
            "COGNIX_B2_BUCKET": "test-bucket",
            "COGNIX_B2_KEY_ID": "test-key",
            "COGNIX_B2_APPLICATION_KEY": "test-secret",
            "COGNIX_B2_REGION": "us-east-005",
        }
        with patch.dict(os.environ, env, clear=True):
            storage = B2ObjectStorage()

        self.assertEqual(storage.region, "us-east-005")


if __name__ == "__main__":
    unittest.main()
