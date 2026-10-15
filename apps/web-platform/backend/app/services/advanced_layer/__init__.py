"""Phase 16 — Advanced Layer runtime.

Exports wiki entity, growth metric, offline handoff contracts, and
secret vault helpers used by the advanced_layer_service and router.
"""
from __future__ import annotations

from .contracts import WikiEntity, GrowthMetric, OfflineHandoff
from .vault import SecretRef, BreachCheckRequest, validate_secret_ref, validate_breach_prefix

__all__ = [
    # Contracts
    "WikiEntity",
    "GrowthMetric",
    "OfflineHandoff",
    # Vault
    "SecretRef",
    "BreachCheckRequest",
    "validate_secret_ref",
    "validate_breach_prefix",
]
