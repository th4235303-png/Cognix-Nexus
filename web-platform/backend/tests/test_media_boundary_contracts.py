import unittest

from app.services.media_boundary.contracts import (
    MediaAsset,
    NativeCapability,
    OCRResult,
    media_lineage_is_valid,
)


class MediaBoundaryContractTests(unittest.TestCase):
    def test_ocr_preserves_owner_and_source_lineage(self):
        asset = MediaAsset(
            id="asset-1",
            owner_id="owner-1",
            storage_ref="storage://asset-1",
            content_sha256="hash",
            source_ref="book:1",
        )
        result = OCRResult(
            asset_id="asset-1",
            owner_id="owner-1",
            text="text",
            source_ref="book:1",
            provider="ocr-test",
        )
        self.assertTrue(media_lineage_is_valid(asset, result))

    def test_cross_owner_ocr_fails_closed(self):
        asset = MediaAsset(
            id="asset-1",
            owner_id="owner-1",
            storage_ref="storage://asset-1",
            content_sha256="hash",
            source_ref="book:1",
        )
        result = OCRResult(
            asset_id="asset-1",
            owner_id="owner-2",
            text="text",
            source_ref="book:1",
            provider="ocr-test",
        )
        self.assertFalse(media_lineage_is_valid(asset, result))

    def test_native_capabilities_remain_explicit_device_gates(self):
        capability = NativeCapability(name="camera", enabled=True)
        self.assertTrue(capability.requires_device_gate)


if __name__ == "__main__":
    unittest.main()
