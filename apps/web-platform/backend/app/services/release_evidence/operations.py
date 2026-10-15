from __future__ import annotations

"""Phase 20 production-operations evidence contracts."""

from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class RecoveryDrill:
    drill_id: str
    kind: Literal["backup_restore","rollback","failover"]
    observed: bool
    recovered: bool
    evidence_ref: str | None = None

def recovery_is_evidenced(drill: RecoveryDrill) -> bool:
    return drill.observed and drill.recovered and bool(drill.evidence_ref)
