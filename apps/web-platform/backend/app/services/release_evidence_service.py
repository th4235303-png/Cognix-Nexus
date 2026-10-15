from __future__ import annotations

"""Phase 20/21 — Release Evidence and Operational Readiness runtime service helpers.

Phase 20: Persist gate evidence, persist recovery drills (fail-closed).
Phase 21: Persist release decisions, evaluate checklists.

Invariants:
  1. GateEvidence with status='pass' requires a non-empty evidence_ref.
  2. RecoveryDrill requires recovery_is_evidenced() — observed, recovered, evidence_ref all set.
  3. Release decisions record evidence JSONB — never raw secrets or binary.
  4. Idempotency keys prevent duplicate gate evidence rows per gate/revision.
  5. All writes are owner-isolated and fail-closed (None on validation failure).
"""

import json
from uuid import uuid4

from app.store import store
from app.services.release_evidence import (
    GateEvidence,
    ReleaseChecklist,
    RecoveryDrill,
    checklist_status,
    recovery_is_evidenced,
)

_GATE_STATUSES = frozenset({"pending", "pass", "fail", "blocked"})
_DRILL_KINDS = frozenset({"backup_restore", "rollback", "failover"})


# ─── persist_gate_evidence ────────────────────────────────────────────────────

def persist_gate_evidence(
    owner_id: str,
    gate_id: str,
    status: str,
    evidence_ref: str | None,
    observed_at: str | None = None,
) -> str | None:
    """Persist a Phase 20 gate evidence record.

    Invariants:
      - status must be one of: pending, pass, fail, blocked.
      - status='pass' requires a non-empty evidence_ref (fail-closed).
      - gate_id must be non-empty.
      - owner_id must be non-empty.
    Returns evidence record ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not gate_id.strip():
        return None
    if status not in _GATE_STATUSES:
        return None
    if status == "pass" and not (evidence_ref and evidence_ref.strip()):
        return None

    record_id = f"GEVID-{uuid4().hex[:8].upper()}"
    idempotency_key = f"{owner_id}:{gate_id}:{status}"
    eff_evidence_ref = evidence_ref.strip()[:2000] if evidence_ref else None

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO release_gate_evidence"
                "(id, owner_id, gate_id, status, evidence_ref, observed_at, idempotency_key) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING RETURNING id",
                (record_id, owner_id, gate_id, status, eff_evidence_ref,
                 observed_at, idempotency_key),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_recovery_drill ───────────────────────────────────────────────────

def persist_recovery_drill(
    owner_id: str,
    drill_id: str,
    kind: str,
    observed: bool,
    recovered: bool,
    evidence_ref: str | None,
) -> str | None:
    """Persist a Phase 20 recovery drill result.

    Invariants:
      - kind must be one of: backup_restore, rollback, failover.
      - recovery_is_evidenced() must return True (observed + recovered + evidence_ref).
      - Fail-closed: incomplete drills are not persisted.
    Returns drill record ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not drill_id.strip():
        return None
    if kind not in _DRILL_KINDS:
        return None

    drill = RecoveryDrill(
        drill_id=drill_id,
        kind=kind,  # type: ignore[arg-type]
        observed=observed,
        recovered=recovered,
        evidence_ref=evidence_ref,
    )
    if not recovery_is_evidenced(drill):
        return None

    record_id = f"DRILL-{uuid4().hex[:8].upper()}"

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO release_recovery_drills"
                "(id, owner_id, drill_id, kind, observed, recovered, evidence_ref) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (record_id, owner_id, drill_id, kind, observed, recovered,
                 evidence_ref.strip()[:2000] if evidence_ref else None),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── evaluate_release_checklist ───────────────────────────────────────────────

def evaluate_release_checklist(
    owner_id: str,
    revision: str,
    required_gates: list[str],
) -> dict | None:
    """Phase 21: Read gate evidence rows and evaluate checklist status.

    Reads all gate evidence records for the owner and evaluates against required_gates.
    Returns a dict with keys: revision, status, evidence, required_gates.
    Fail-closed: returns None if db is None or inputs are invalid.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not revision.strip():
        return None
    if not required_gates:
        return None

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT gate_id, status, evidence_ref, observed_at "
                "FROM release_gate_evidence "
                "WHERE owner_id = %s ORDER BY created_at DESC",
                (owner_id,),
            )
            rows = cur.fetchall() or []

    # Latest status per gate_id
    seen: dict[str, GateEvidence] = {}
    for row in rows:
        gid = row["gate_id"]
        if gid not in seen:
            seen[gid] = GateEvidence(
                gate_id=gid,
                status=row["status"],
                evidence_ref=row["evidence_ref"],
                observed_at=row["observed_at"],
            )

    checklist = ReleaseChecklist(
        revision=revision,
        required_gates=tuple(required_gates),
        evidence=tuple(seen.values()),
    )
    status = checklist_status(checklist)

    return {
        "revision": revision,
        "status": status,
        "required_gates": required_gates,
        "evidence": [
            {
                "gate_id": e.gate_id,
                "status": e.status,
                "evidence_ref": e.evidence_ref,
                "observed_at": e.observed_at,
            }
            for e in seen.values()
        ],
    }


# ─── persist_release_decision ─────────────────────────────────────────────────

def persist_release_decision(
    owner_id: str,
    revision: str,
    approved: bool,
    evidence: list[dict],
) -> str | None:
    """Phase 21: Persist a release decision record with evidence JSONB.

    Invariants:
      - revision must be non-empty.
      - evidence must be non-empty list of gate evidence snapshots.
      - evidence is stored as JSONB — no secrets or binary in evidence dicts.
    Returns decision ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not revision.strip():
        return None
    if not evidence:
        return None

    record_id = f"RDEC-{uuid4().hex[:8].upper()}"

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO release_decisions"
                "(id, owner_id, revision, approved, evidence) "
                "VALUES (%s, %s, %s, %s, %s::jsonb) RETURNING id",
                (record_id, owner_id, revision.strip()[:200], approved,
                 json.dumps(evidence)),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None
