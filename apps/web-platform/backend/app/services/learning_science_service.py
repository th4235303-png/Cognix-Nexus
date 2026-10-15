from __future__ import annotations

"""Phase 14 — Learning Science runtime service helpers.

Functions in this module are the only place that writes to
learning_science DB tables.  They are designed to be:
  - Idempotent (ON CONFLICT DO NOTHING on idempotency_key)
  - Evidence-required (fail-closed — no evidence → no record)
  - Owner-isolated (every INSERT/SELECT scoped to owner_id)
  - No-op when store.database is None (in-memory mode)

Invariants:
  1. No learning path becomes active without an explicit reason.
  2. Evidence refs must be attached to every persisted signal.
  3. decay_weight() is deterministic and cannot be overridden at runtime.
  4. Signals are append-only; no UPDATE of existing signals.
"""

import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from app.store import store
from app.services.learning_science import (
    LearningSignal,
    LearningPathItem,
    LearningCandidate,
    build_path,
    decay_weight,
)

_SIGNAL_TYPES = frozenset({"review", "recall", "completion", "difficulty", "reflection"})


# ─── persist_learning_signal ─────────────────────────────────────────────────

def persist_learning_signal(
    owner_id: str,
    subject_id: str,
    signal_type: str,
    strength: float,
    evidence_refs: list[dict],
    idempotency_key: str,
    occurred_at: datetime | None = None,
) -> str | None:
    """Persist a Phase 14 LearningSignal to the database.

    Invariants enforced:
      - strength must be in [0.0, 1.0]
      - signal_type must be a known type
      - evidence_refs must be non-empty (fail-closed)
      - idempotency_key must be non-empty
      - owner_id and subject_id must be non-empty

    Returns the signal ID, or None if validation fails or DB unavailable.
    ON CONFLICT on idempotency_key returns the existing signal ID (idempotent).
    """
    db = store.database
    if db is None:
        return None

    # Validate inputs.
    if not owner_id.strip() or not subject_id.strip():
        return None
    if signal_type not in _SIGNAL_TYPES:
        return None
    if not (0.0 <= strength <= 1.0):
        return None
    if not evidence_refs:
        return None
    if not idempotency_key.strip():
        return None

    signal_id = f"LSIG-{uuid4().hex[:8].upper()}"
    ts = (occurred_at or datetime.now(timezone.utc)).isoformat()

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO learning_signals"
                "(id, owner_id, subject_id, signal_type, strength, evidence_refs, idempotency_key, occurred_at) "
                "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING RETURNING id",
                (
                    signal_id, owner_id, subject_id, signal_type,
                    float(strength),
                    json.dumps(evidence_refs),
                    idempotency_key, ts,
                ),
            )
            row = cur.fetchone()
            if row is None:
                # Idempotency hit — fetch existing id.
                cur.execute(
                    "SELECT id FROM learning_signals WHERE idempotency_key = %s AND owner_id = %s",
                    (idempotency_key, owner_id),
                )
                row = cur.fetchone()
        conn.commit()

    return row["id"] if row else None


# ─── persist_learning_path ────────────────────────────────────────────────────

def persist_learning_path(
    owner_id: str,
    items: list[LearningPathItem],
) -> list[str]:
    """Persist a ranked list of LearningPathItems to the database.

    Each item must carry at least one evidence_ref and a non-empty reason.
    Items that fail validation are skipped (partial success is acceptable;
    the caller should verify the returned ID list).

    Returns list of persisted path-item IDs (may be shorter than input if
    some items fail validation or DB is unavailable).
    """
    db = store.database
    if db is None:
        return []
    if not owner_id.strip() or not items:
        return []

    inserted_ids: list[str] = []
    with db.connect() as conn:
        with conn.cursor() as cur:
            for item in items:
                if not item.reason.strip():
                    continue
                if not item.evidence_refs:
                    continue
                if not item.subject_id.strip():
                    continue
                item_id = f"LPATH-{uuid4().hex[:8].upper()}"
                cur.execute(
                    "INSERT INTO learning_path_items"
                    "(id, owner_id, subject_id, position, reason, evidence_refs) "
                    "VALUES (%s, %s, %s, %s, %s, %s::jsonb)",
                    (
                        item_id, owner_id, item.subject_id,
                        int(item.position), item.reason[:2000],
                        json.dumps(list(item.evidence_refs)),
                    ),
                )
                inserted_ids.append(item_id)
        conn.commit()

    return inserted_ids


# ─── build_path_from_db ───────────────────────────────────────────────────────

def build_path_from_db(
    owner_id: str,
    half_life_days: float = 14.0,
    limit: int = 10,
) -> tuple[LearningPathItem, ...]:
    """Load recent learning signals from DB and compute a priority-ranked path.

    Uses decay_weight(age_days, half_life_days) × weakness to rank subjects.
    Pure deterministic output — no LLM, no side effects.

    Returns empty tuple when DB unavailable or no signals exist.
    """
    db = store.database
    if db is None:
        return ()
    if not owner_id.strip():
        return ()

    limit = max(1, min(limit, 50))
    now = datetime.now(timezone.utc)

    with db.connect() as conn:
        with conn.cursor() as cur:
            # Aggregate per subject: average difficulty as weakness proxy,
            # most recent signal age.  Only look at the last 90 days.
            cur.execute(
                """
                SELECT
                    subject_id,
                    AVG(CASE WHEN signal_type = 'difficulty' THEN strength ELSE 0 END) AS weakness,
                    MAX(occurred_at) AS last_seen,
                    array_agg(id ORDER BY occurred_at DESC) AS signal_ids
                FROM learning_signals
                WHERE owner_id = %s
                  AND occurred_at >= now() - INTERVAL '90 days'
                GROUP BY subject_id
                HAVING COUNT(*) >= 1
                ORDER BY weakness DESC
                LIMIT %s
                """,
                (owner_id, limit * 3),  # fetch extra to allow decay re-ranking
            )
            rows = cur.fetchall()

    if not rows:
        return ()

    candidates: list[LearningCandidate] = []
    for row in rows:
        last_seen = row.get("last_seen")
        if last_seen is None:
            continue
        if isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen)
        # Make tz-aware if naive.
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        age_days = max(0.0, (now - last_seen).total_seconds() / 86400)
        signal_ids = tuple(str(s) for s in (row.get("signal_ids") or [])[:5])

        try:
            c = LearningCandidate(
                subject_id=str(row["subject_id"]),
                weakness=float(row.get("weakness") or 0.0),
                age_days=age_days,
                half_life_days=max(1.0, half_life_days),
                evidence_refs=signal_ids,
            )
            candidates.append(c)
        except (ValueError, KeyError):
            continue

    return build_path(tuple(candidates), limit)
