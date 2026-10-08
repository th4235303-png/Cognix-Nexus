from __future__ import annotations

"""Phase 18 metadata normalization helpers."""

from dataclasses import dataclass

@dataclass(frozen=True)
class MediaMetadata:
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None
    captured_at: str | None = None
    title: str | None = None

def metadata_is_safe(metadata: MediaMetadata) -> bool:
    return (metadata.width is None or metadata.width > 0) and (metadata.height is None or metadata.height > 0)
