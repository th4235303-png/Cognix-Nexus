from __future__ import annotations

"""Phase 16 privacy-bound secret and offline handoff contracts."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class SecretRef:
    id: str
    owner_id: str
    kind: Literal["totp", "ssh_key", "credential"]
    ciphertext_ref: str

@dataclass(frozen=True)
class BreachCheckRequest:
    owner_id: str
    secret_digest_prefix: str

def validate_secret_ref(secret: SecretRef) -> bool:
    return bool(secret.id.strip() and secret.owner_id.strip() and secret.ciphertext_ref.strip())

def validate_breach_prefix(request: BreachCheckRequest) -> bool:
    return bool(request.owner_id.strip() and len(request.secret_digest_prefix) in {5, 6})
