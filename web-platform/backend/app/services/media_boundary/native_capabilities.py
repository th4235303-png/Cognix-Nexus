from __future__ import annotations

"""Phase 19 explicit device-capability gate helpers."""

from dataclasses import dataclass
from typing import Literal

Capability = Literal["camera","voice","push","biometric","offline"]

@dataclass(frozen=True)
class DeviceGate:
    capability: Capability
    device_verified: bool
    user_enabled: bool

def capability_is_activatable(gate: DeviceGate) -> bool:
    return gate.device_verified and gate.user_enabled
