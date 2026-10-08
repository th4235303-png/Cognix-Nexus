from __future__ import annotations

"""Privacy-first Phase 15 life-integration contracts."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ContextRestoreRequest:
    id: str
    owner_id: str
    requested_by_user: bool
    scope: tuple[str, ...]
    reason: str

@dataclass(frozen=True)
class PrivacyBoundary:
    data_class: Literal["user_content", "private_signal", "encrypted_capsule"]
    owner_id: str
    retention: Literal["session", "explicitly_saved", "user_deleted"]
    cross_feature: bool = False

@dataclass(frozen=True)
class EncryptedCapsuleRef:
    id: str
    owner_id: str
    ciphertext_ref: str
    algorithm: str
    exportable: bool = True

def can_restore(request: ContextRestoreRequest) -> bool:
    return bool(request.owner_id and request.requested_by_user and request.scope)
