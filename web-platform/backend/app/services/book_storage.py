from __future__ import annotations

import os
from pathlib import Path


class BookBinaryStorage:
    """Storage boundary for original book binaries.

    The database stores metadata/text, never the original binary. Configure
    COGNIX_BOOK_STORAGE_DIR to a persistent volume (or replace this adapter
    with object/Drive storage without changing ingestion APIs).
    """

    def __init__(self, root: str | None = None):
        self.root = Path(root or os.getenv("COGNIX_BOOK_STORAGE_DIR", "")).expanduser()

    @property
    def configured(self) -> bool:
        return bool(str(self.root))

    def put(self, book_id: str, filename: str, data: bytes) -> str:
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        safe_name = Path(filename).name or "document"
        target_dir = self.root / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / safe_name
        target.write_bytes(data)
        return str(target)

    def get(self, book_id: str, filename: str) -> bytes:
        if not self.configured:
            raise RuntimeError("COGNIX_BOOK_STORAGE_DIR is not configured")
        target = self.root / book_id / (Path(filename).name or "document")
        return target.read_bytes()
