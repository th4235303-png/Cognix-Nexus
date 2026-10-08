from __future__ import annotations

"""Phase 15 explicit restore policy. No implicit context activation."""

from dataclasses import dataclass
from .contracts import ContextRestoreRequest, PrivacyBoundary, can_restore

@dataclass(frozen=True)
class RestoreDecision:
    allowed: bool
    reason: str

def authorize_restore(request: ContextRestoreRequest, boundary: PrivacyBoundary) -> RestoreDecision:
    if not can_restore(request):
        return RestoreDecision(False, "user-triggered restore, owner and scope are required")
    if boundary.owner_id != request.owner_id:
        return RestoreDecision(False, "owner mismatch")
    if boundary.cross_feature:
        return RestoreDecision(False, "cross-feature restore is not implicit")
    return RestoreDecision(True, "explicit restore authorized")
