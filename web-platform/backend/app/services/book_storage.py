from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.services.object_storage import b2_storage, r2_storage


class BookBinaryStorage:
    """Original-binary storage with local, Backblaze B2, or legacy R2 backends."""

    def __init__(self, root: str | None = None):
        self.provider = os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower()
        configured_root = root if root is not None else os.getenv("COGNIX_BOOK_STORAGE_DIR", "")
        self.root = Path(configured_root).expanduser() if configured_root else None

    @property
    def configured(self) -> bool:
        if self.provider == "b2":
            return b2_storage().configured
        if self.provider == "r2":
            return r2_storage().configured
        return self.root is not None

    def _object_storage(self):
        if self.provider == "b2":
            return b2_storage()
        if self.provider == "r2":
            return r2_storage()
        return None

    def put(self, book_id: str, filename: str, data: bytes) -> str:
        safe_name = Path(filename).name or "document"
        storage = self._object_storage()
        if storage:
            return storage.put_bytes(f"books/{book_id}/{safe_name}", data).key
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        target_dir = self.root / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe_name
        target.write_bytes(data)
        return str(target)

    def get(self, book_id: str, filename: str) -> bytes:
        safe_name = Path(filename).name or "document"
        storage = self._object_storage()
        if storage:
            return storage.get_bytes(f"books/{book_id}/{safe_name}")
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        return (self.root / book_id / safe_name).read_bytes()

    def checksum(self, book_id: str, filename: str) -> str:
        return hashlib.sha256(self.get(book_id, filename)).hexdigest()

    def delete(self, book_id: str, filename: str) -> None:
        safe_name = Path(filename).name or "document"
        storage = self._object_storage()
        if storage:
            storage.delete(f"books/{book_id}/{safe_name}")
            return
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        target = self.root / book_id / safe_name
        if target.exists():
            target.unlink()
