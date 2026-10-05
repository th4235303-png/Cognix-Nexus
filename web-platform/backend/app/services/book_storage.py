from __future__ import annotations

import hashlib
import os
from pathlib import Path

from app.services.object_storage import b2_storage, cloudinary_storage, r2_storage, supabase_storage


class BookBinaryStorage:
    """Tiered original storage: Supabase Storage <= threshold, B2 above it."""

    def __init__(self, root: str | None = None):
        self.provider = os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "tiered").strip().lower()
        configured_root = root if root is not None else os.getenv("COGNIX_BOOK_STORAGE_DIR", "")
        self.root = Path(configured_root).expanduser() if configured_root else None
        self.threshold_bytes = max(
            1,
            int(os.getenv("COGNIX_B2_LARGE_FILE_THRESHOLD_BYTES", str(50 * 1024 * 1024))),
        )

    @property
    def configured(self) -> bool:
        if self.provider in {"tiered", "hybrid"}:
            return supabase_storage().configured and b2_storage().configured
        if self.provider == "b2":
            return b2_storage().configured
        if self.provider == "supabase":
            return supabase_storage().configured
        if self.provider == "cloudinary":
            return cloudinary_storage().configured
        if self.provider == "r2":
            return r2_storage().configured
        return self.root is not None

    def _storage_for_put(self, data: bytes):
        if self.provider in {"tiered", "hybrid"}:
            return b2_storage() if len(data) > self.threshold_bytes else supabase_storage()
        if self.provider == "b2":
            return b2_storage()
        if self.provider == "supabase":
            return supabase_storage()
        if self.provider == "cloudinary":
            return cloudinary_storage()
        if self.provider == "r2":
            return r2_storage()
        return None

    @staticmethod
    def _unwrap_key(stored_key: str):
        for prefix, factory in (
            ("b2://", b2_storage),
            ("supabase://", supabase_storage),
            ("cloudinary://", cloudinary_storage),
            ("r2://", r2_storage),
        ):
            if stored_key.startswith(prefix):
                return factory(), stored_key.removeprefix(prefix)
        return None, stored_key

    def put(self, book_id: str, filename: str, data: bytes) -> str:
        safe_name = Path(filename).name or "document"
        storage = self._storage_for_put(data)
        if storage:
            content_type = {
                "pdf": "application/pdf",
                "epub": "application/epub+zip",
            }.get(Path(safe_name).suffix.lower().lstrip("."), "application/octet-stream")
            stored = storage.put_bytes(
                f"books/{book_id}/{safe_name}",
                data,
                content_type=content_type,
            )
            prefix = (
                "b2://" if isinstance(storage, type(b2_storage()))
                else "supabase://" if isinstance(storage, type(supabase_storage()))
                else "cloudinary://" if isinstance(storage, type(cloudinary_storage()))
                else "r2://"
            )
            return stored.key if stored.key.startswith("cloudinary://") else f"{prefix}{stored.key}"
        if not self.configured:
            raise RuntimeError("Book storage is not configured")
        target_dir = self.root / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe_name
        target.write_bytes(data)
        return str(target)

    def get(self, book_id: str, filename: str, stored_key: str | None = None) -> bytes:
        safe_name = Path(filename).name or "document"
        if stored_key:
            storage, key = self._unwrap_key(stored_key)
            if storage:
                return storage.get_bytes(key)
        if self.provider in {"tiered", "hybrid"}:
            # Legacy rows may contain an unprefixed key; try the small-file tier first,
            # then the large-file tier without weakening authorization.
            for storage in (supabase_storage(), b2_storage()):
                try:
                    return storage.get_bytes(stored_key or f"books/{book_id}/{safe_name}")
                except Exception:
                    continue
            raise RuntimeError("Stored book object could not be read")
        storage = self._storage_for_put(b"")
        if storage:
            return storage.get_bytes(stored_key or f"books/{book_id}/{safe_name}")
        if not self.configured:
            raise RuntimeError("Book storage is not configured")
        return (self.root / book_id / safe_name).read_bytes()

    def checksum(self, book_id: str, filename: str, stored_key: str | None = None) -> str:
        return hashlib.sha256(self.get(book_id, filename, stored_key=stored_key)).hexdigest()

    def delete(self, book_id: str, filename: str, stored_key: str | None = None) -> None:
        safe_name = Path(filename).name or "document"
        if stored_key:
            storage, key = self._unwrap_key(stored_key)
            if storage:
                storage.delete(key)
                return
        if self.provider in {"tiered", "hybrid"}:
            key = stored_key or f"books/{book_id}/{safe_name}"
            for storage in (supabase_storage(), b2_storage()):
                try:
                    storage.delete(key)
                    return
                except Exception:
                    continue
            return
        storage = self._storage_for_put(b"")
        if storage:
            storage.delete(stored_key or f"books/{book_id}/{safe_name}")
            return
        if not self.configured:
            raise RuntimeError("Book storage is not configured")
        target = self.root / book_id / safe_name
        if target.exists():
            target.unlink()
