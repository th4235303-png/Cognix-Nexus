from __future__ import annotations

"""Phase 16 — Advanced Layer runtime service helpers.

Invariants:
  1. WikiEntity requires at least one source_ref (lineage required).
  2. GrowthMetric requires a derivation explanation and at least one evidence_ref.
  3. OfflineHandoff stores only an artifact_ref (URI) — never the artifact payload.
  4. SecretRef stores only ciphertext_ref — never raw secrets or plaintext.
  5. BreachCheckRequest sends only a 5-6 char digest prefix — never the full hash/value.
  6. All writes are owner-isolated and fail-closed (None/[] on any validation failure).
"""

import json
from uuid import uuid4

from app.store import store
from app.services.advanced_layer import (
    WikiEntity,
    GrowthMetric,
    OfflineHandoff,
    SecretRef,
    BreachCheckRequest,
    validate_secret_ref,
    validate_breach_prefix,
)

_HANDOFF_FORMATS = frozenset({"encrypted_archive", "signed_manifest"})
_SECRET_KINDS = frozenset({"totp", "ssh_key", "credential"})
_ENTITY_TYPES = frozenset({
    "person", "organization", "place", "concept", "technology",
    "event", "product", "book", "term", "other",
})


# ─── persist_wiki_entity ──────────────────────────────────────────────────────

def persist_wiki_entity(
    owner_id: str,
    name: str,
    entity_type: str,
    source_refs: list[str],
) -> str | None:
    """Persist a Phase 16 WikiEntity with source lineage.

    Invariant: source_refs must be non-empty (lineage required — fail-closed).
    Returns entity ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not name.strip():
        return None
    if entity_type not in _ENTITY_TYPES:
        return None
    if not source_refs:
        return None

    entity = WikiEntity(
        id=f"WIKI-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        name=name.strip()[:500],
        entity_type=entity_type,
        source_refs=tuple(source_refs[:20]),
    )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO advanced_wiki_entities"
                "(id, owner_id, name, entity_type, source_refs) "
                "VALUES (%s, %s, %s, %s, %s::jsonb) RETURNING id",
                (entity.id, owner_id, entity.name, entity_type, json.dumps(list(entity.source_refs))),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_growth_metric ────────────────────────────────────────────────────

def persist_growth_metric(
    owner_id: str,
    metric: str,
    value: float,
    unit: str,
    evidence_refs: list[str],
    derivation: str,
) -> str | None:
    """Persist a Phase 16 GrowthMetric with derivation and evidence.

    Invariants:
      - evidence_refs must be non-empty (fail-closed)
      - derivation must be non-empty (explainability required)
      - metric and unit must be non-empty
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not metric.strip() or not unit.strip():
        return None
    if not evidence_refs:
        return None
    if not derivation.strip():
        return None

    gm = GrowthMetric(
        id=f"GMET-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        metric=metric.strip()[:200],
        value=float(value),
        unit=unit.strip()[:50],
        evidence_refs=tuple(evidence_refs[:20]),
        derivation=derivation.strip()[:2000],
    )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO advanced_growth_metrics"
                "(id, owner_id, metric, value, unit, evidence_refs, derivation) "
                "VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s) RETURNING id",
                (
                    gm.id, owner_id, gm.metric, gm.value, gm.unit,
                    json.dumps(list(gm.evidence_refs)), gm.derivation,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_offline_handoff ──────────────────────────────────────────────────

def persist_offline_handoff(
    owner_id: str,
    format: str,
    artifact_ref: str,
    recoverable: bool = True,
) -> str | None:
    """Persist a Phase 16 OfflineHandoff — artifact_ref only, never payload.

    Invariants:
      - format must be 'encrypted_archive' or 'signed_manifest'
      - artifact_ref is a URI/key reference — payload is NEVER stored here
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not artifact_ref.strip():
        return None
    if format not in _HANDOFF_FORMATS:
        return None

    handoff = OfflineHandoff(
        id=f"OHOFF-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        format=format,  # type: ignore[arg-type]
        artifact_ref=artifact_ref.strip()[:2000],
        recoverable=recoverable,
    )

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO advanced_offline_handoffs"
                "(id, owner_id, format, artifact_ref, recoverable) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (handoff.id, owner_id, format, handoff.artifact_ref, recoverable),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_secret_ref ───────────────────────────────────────────────────────

def persist_secret_ref(
    owner_id: str,
    kind: str,
    ciphertext_ref: str,
) -> str | None:
    """Persist a SecretRef — ciphertext_ref URI only, never raw secret/plaintext.

    Invariants:
      - kind must be 'totp', 'ssh_key', or 'credential'
      - ciphertext_ref is a URI — raw secrets are NEVER passed through this function
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not ciphertext_ref.strip():
        return None
    if kind not in _SECRET_KINDS:
        return None

    secret = SecretRef(
        id=f"SREF-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        kind=kind,  # type: ignore[arg-type]
        ciphertext_ref=ciphertext_ref.strip()[:2000],
    )

    if not validate_secret_ref(secret):
        return None

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO advanced_secret_refs"
                "(id, owner_id, kind, ciphertext_ref) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (secret.id, owner_id, kind, secret.ciphertext_ref),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None
