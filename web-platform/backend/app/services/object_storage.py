from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import boto3
import httpx
from botocore.config import Config


@dataclass(frozen=True)
class StoredObject:
    key: str
    checksum: str
    size: int


class S3ObjectStorage:
    """Shared S3-compatible adapter used by B2 and the legacy R2 integration."""

    def __init__(self, *, label: str, endpoint_env: str, bucket_env: str, access_env: str, secret_env: str, region_env: str, default_region: str):
        self.label = label
        self.endpoint = os.getenv(endpoint_env, "").strip().rstrip("/")
        self.bucket = os.getenv(bucket_env, "").strip()
        self.access_key = os.getenv(access_env, "").strip()
        self.secret_key = os.getenv(secret_env, "").strip()
        self.region = os.getenv(region_env, default_region).strip() or default_region

    @property
    def configured(self) -> bool:
        return all((self.endpoint, self.bucket, self.access_key, self.secret_key))

    def _client(self):
        if not self.configured:
            raise RuntimeError(f"{self.label} object storage is not configured")
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
        return hashlib.sha256(self.get_bytes(key)).hexdigest().lower() == expected_sha256.lower()


class R2ObjectStorage(S3ObjectStorage):
    """Backward-compatible Cloudflare R2 adapter."""

    def __init__(self) -> None:
        super().__init__(label="Cloudflare R2", endpoint_env="COGNIX_R2_ENDPOINT", bucket_env="COGNIX_R2_BUCKET", access_env="COGNIX_R2_ACCESS_KEY_ID", secret_env="COGNIX_R2_SECRET_ACCESS_KEY", region_env="COGNIX_R2_REGION", default_region="auto")


class B2ObjectStorage(S3ObjectStorage):
    """Backblaze B2 S3-compatible object storage."""

    def __init__(self) -> None:
        super().__init__(label="Backblaze B2", endpoint_env="COGNIX_B2_ENDPOINT", bucket_env="COGNIX_B2_BUCKET", access_env="COGNIX_B2_KEY_ID", secret_env="COGNIX_B2_APPLICATION_KEY", region_env="COGNIX_B2_REGION", default_region="us-east-005")


class SupabaseObjectStorage:
    """Supabase Storage adapter using a backend-only service-role key."""

    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        self.bucket = os.getenv("COGNIX_SUPABASE_STORAGE_BUCKET", "").strip()
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    @property
    def configured(self) -> bool:
        return all((self.url, self.bucket, self.service_key))

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        if not self.configured:
            raise RuntimeError("Supabase Storage is not configured")
        headers = {"Authorization": f"Bearer {self.service_key}", "apikey": self.service_key}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _url(self, key: str) -> str:
        return f"{self.url}/storage/v1/object/{self.bucket}/{key.lstrip('/')}"

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> StoredObject:
        checksum = hashlib.sha256(data).hexdigest()
        headers = self._headers(content_type)
        headers["x-upsert"] = "true"
        response = httpx.post(self._url(key), content=data, headers=headers, timeout=30)
        response.raise_for_status()
        return StoredObject(key=key, checksum=checksum, size=len(data))

    def get_bytes(self, key: str) -> bytes:
        response = httpx.get(self._url(key), headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.content

    def delete(self, key: str) -> None:
        response = httpx.delete(self._url(key), headers=self._headers(), timeout=30)
        response.raise_for_status()

    def verify(self, key: str, expected_sha256: str) -> bool:
        return hashlib.sha256(self.get_bytes(key)).hexdigest().lower() == expected_sha256.lower()


def r2_storage() -> R2ObjectStorage:
    return R2ObjectStorage()


def b2_storage() -> B2ObjectStorage:
    return B2ObjectStorage()


def supabase_storage() -> SupabaseObjectStorage:
    return SupabaseObjectStorage()
