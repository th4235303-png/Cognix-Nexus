from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import BinaryIO

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class StoredObject:
    key: str
    checksum: str
    size: int


class R2ObjectStorage:
    """Cloudflare R2 S3-compatible object storage adapter.

    Credentials are read only from the environment. The adapter is intentionally
    provider-neutral at the call site and returns content hashes for restore checks.
    """

    def __init__(self) -> None:
        self.endpoint = os.getenv("COGNIX_R2_ENDPOINT", "").strip().rstrip("/")
        self.bucket = os.getenv("COGNIX_R2_BUCKET", "").strip()
        self.access_key = os.getenv("COGNIX_R2_ACCESS_KEY_ID", "").strip()
        self.secret_key = os.getenv("COGNIX_R2_SECRET_ACCESS_KEY", "").strip()
        self.region = os.getenv("COGNIX_R2_REGION", "auto").strip() or "auto"

    @property
    def configured(self) -> bool:
        return all((self.endpoint, self.bucket, self.access_key, self.secret_key))

    def _client(self):
        if not self.configured:
            raise RuntimeError("Cloudflare R2 is not configured")
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> StoredObject:
        checksum = hashlib.sha256(data).hexdigest()
        extra = {"ChecksumSHA256": checksum}
        if content_type:
            extra["ContentType"] = content_type
        self._client().put_object(Bucket=self.bucket, Key=key, Body=data, **extra)
        return StoredObject(key=key, checksum=checksum, size=len(data))

    def get_bytes(self, key: str) -> bytes:
        response = self._client().get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def head(self, key: str) -> dict:
        return self._client().head_object(Bucket=self.bucket, Key=key)

    def delete(self, key: str) -> None:
        self._client().delete_object(Bucket=self.bucket, Key=key)

    def verify(self, key: str, expected_sha256: str) -> bool:
        data = self.get_bytes(key)
        return hashlib.sha256(data).hexdigest().lower() == expected_sha256.lower()


def r2_storage() -> R2ObjectStorage:
    return R2ObjectStorage()
