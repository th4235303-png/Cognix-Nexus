"""Phase 15 — Life Integration runtime.

Exports privacy-first contracts, restore policy, and capsule helpers used
by the life_integration_service layer and the router.
"""
from __future__ import annotations

from .contracts import (
    ContextRestoreRequest,
    PrivacyBoundary,
    EncryptedCapsuleRef,
    can_restore,
)
from .restore import RestoreDecision, authorize_restore

__all__ = [
    # Contracts
    "ContextRestoreRequest",
    "PrivacyBoundary",
    "EncryptedCapsuleRef",
    "can_restore",
    # Restore policy
    "RestoreDecision",
    "authorize_restore",
]
