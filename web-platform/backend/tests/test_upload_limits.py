import asyncio
import unittest

from app.services.upload_limits import UploadTooLargeError, read_upload_limited


MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class FakeAsyncUpload:
    def __init__(self, size: int):
        self.size = size
        self.requested_sizes: list[int] = []
        self.bytes_returned = 0

    async def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        count = min(size, self.size - self.bytes_returned)
        self.bytes_returned += count
        return b"x" * count


class UploadLimitTests(unittest.TestCase):
    def test_at_limit_upload_is_accepted_with_bounded_read(self):
        upload = FakeAsyncUpload(MAX_UPLOAD_BYTES)

        data = asyncio.run(read_upload_limited(upload, MAX_UPLOAD_BYTES))

        self.assertEqual(len(data), MAX_UPLOAD_BYTES)
        self.assertEqual(upload.requested_sizes, [MAX_UPLOAD_BYTES + 1])
        self.assertEqual(upload.bytes_returned, MAX_UPLOAD_BYTES)

    def test_over_limit_upload_is_rejected_after_bounded_read(self):
        upload = FakeAsyncUpload(MAX_UPLOAD_BYTES + 10 * 1024 * 1024)

        with self.assertRaises(UploadTooLargeError):
            asyncio.run(read_upload_limited(upload, MAX_UPLOAD_BYTES))

        self.assertEqual(upload.requested_sizes, [MAX_UPLOAD_BYTES + 1])
        self.assertEqual(upload.bytes_returned, MAX_UPLOAD_BYTES + 1)


if __name__ == "__main__":
    unittest.main()
