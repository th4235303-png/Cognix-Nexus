from __future__ import annotations

"""Provider-agnostic Phase 16 advanced-layer contracts."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class WikiEntity:
    id: str
    owner_id: str
    name: str
    entity_type: str
    source_refs: tuple[str, ...] = ()

@dataclass(frozen=True)
class GrowthMetric:
    id: str
    owner_id: str
    metric: str
    value: float
    unit: str
    evidence_refs: tuple[str, ...] = ()
    derivation: str = ""

@dataclass(frozen=True)
class OfflineHandoff:
    id: str
    owner_id: str
    format: Literal["encrypted_archive", "signed_manifest"]
    artifact_ref: str
    recoverable: bool = True
