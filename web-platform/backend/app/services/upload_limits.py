class UploadTooLargeError(ValueError):
    """Raised when an upload exceeds its configured byte limit."""


async def read_upload_limited(upload, max_bytes: int) -> bytes:
    """Read at most one byte beyond the maximum, raising if that byte exists."""
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise UploadTooLargeError
    return data
