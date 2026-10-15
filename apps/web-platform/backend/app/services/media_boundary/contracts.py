from __future__ import annotations

"""Non-runtime Phase 18/19 boundary contracts."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MediaAsset:
    id: str
    owner_id: str
    storage_ref: str
    content_sha256: str
    source_ref: str


@dataclass(frozen=True)
class OCRResult:
    asset_id: str
    owner_id: str
    text: str
    source_ref: str
    provider: str
    status: Literal["draft", "needs_review", "approved", "failed"] = "draft"


@dataclass(frozen=True)
class NativeCapability:
    name: Literal["camera", "voice", "push", "biometric", "offline"]
    enabled: bool
    requires_device_gate: bool = True


def media_lineage_is_valid(asset: MediaAsset, result: OCRResult) -> bool:
    return bool(
        asset.id.strip()
        and asset.owner_id.strip()
        and result.asset_id == asset.id
        and result.owner_id == asset.owner_id
        and result.source_ref == asset.source_ref
    )
