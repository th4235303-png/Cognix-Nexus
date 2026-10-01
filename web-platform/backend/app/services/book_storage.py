from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.services.object_storage import r2_storage


class BookBinaryStorage:
    """Original-binary storage with local or Cloudflare R2 backends."""

    def __init__(self, root: str | None = None):
        self.provider = os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower()
        configured_root = root if root is not None else os.getenv("COGNIX_BOOK_STORAGE_DIR", "")
        self.root = Path(configured_root).expanduser() if configured_root else None

    @property
    def configured(self) -> bool:
        if self.provider == "r2":
            return r2_storage().configured
        return self.root is not None

    def put(self, book_id: str, filename: str, data: bytes) -> str:
        safe_name = Path(filename).name or "document"
        if self.provider == "r2":
            key = f"books/{book_id}/{safe_name}"
            stored = r2_storage().put_bytes(key, data)
            return stored.key
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        target_dir = self.root / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe_name
        target.write_bytes(data)
        return str(target)

    def get(self, book_id: str, filename: str) -> bytes:
        safe_name = Path(filename).name or "document"
        if self.provider == "r2":
            return r2_storage().get_bytes(f"books/{book_id}/{safe_name}")
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        return (self.root / book_id / safe_name).read_bytes()

    def checksum(self, book_id: str, filename: str) -> str:
        return hashlib.sha256(self.get(book_id, filename)).hexdigest()

    def delete(self, book_id: str, filename: str) -> None:
        safe_name = Path(filename).name or "document"
        if self.provider == "r2":
            r2_storage().delete(f"books/{book_id}/{safe_name}")
            return
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        target = self.root / book_id / safe_name
        if target.exists():
            target.unlink()
