from __future__ import annotations

"""Phase 18 media processing planning contracts; no provider calls."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class MediaBatchItem:
    asset_id: str
    owner_id: str
    source_ref: str
    status: Literal["queued","processing","partial","completed","failed"] = "queued"

@dataclass(frozen=True)
class MediaPackageManifest:
    owner_id: str
    asset_ids: tuple[str, ...]
    include_original: bool = True
    include_ocr: bool = True
    include_metadata: bool = True
    include_thumbnail: bool = True

def package_is_valid(manifest: MediaPackageManifest) -> bool:
    return bool(manifest.owner_id.strip() and manifest.asset_ids)
