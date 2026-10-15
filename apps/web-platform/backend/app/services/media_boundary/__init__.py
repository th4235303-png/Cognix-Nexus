"""Phase 18/19 — Media Boundary and Native Capabilities runtime.

Phase 18: Vizora Lens — media asset registration, OCR result persistence,
          evidence-lineage validation, batch processing manifests.
Phase 19: Native/Product UX — device gate contracts and capability tracking.

No provider calls are made here — these are persistence and contract layers only.
Provider failures must be explicit; no silent fallback.
"""
from __future__ import annotations

from .contracts import MediaAsset, OCRResult, NativeCapability, media_lineage_is_valid
from .media_processing import MediaBatchItem, MediaPackageManifest, package_is_valid
from .metadata import MediaMetadata, metadata_is_safe
from .native_capabilities import DeviceGate, capability_is_activatable

__all__ = [
    # Phase 18 — media
    "MediaAsset",
    "OCRResult",
    "NativeCapability",
    "media_lineage_is_valid",
    "MediaBatchItem",
    "MediaPackageManifest",
    "package_is_valid",
    "MediaMetadata",
    "metadata_is_safe",
    # Phase 19 — native
    "DeviceGate",
    "capability_is_activatable",
]
