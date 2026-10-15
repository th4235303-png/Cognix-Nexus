from __future__ import annotations

"""Phase 15 — Life Integration runtime service helpers.

Invariants:
  1. Context restore is ONLY triggered by an explicit user request (requested_by_user=True).
  2. Cross-feature restore is never implicit — always fails closed.
  3. Owner mismatch always fails closed.
  4. Encrypted capsule refs never expose ciphertext — only metadata is persisted.
  5. Consent events are append-only; revocation adds a new event, never deletes.
  6. No ambient/background context activation; only user-triggered restores.
"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.store import store
from app.services.life_integration import (
    ContextRestoreRequest,
    PrivacyBoundary,
    EncryptedCapsuleRef,
    authorize_restore,
    can_restore,
)

_CONSENT_ACTIONS = frozenset({"granted", "revoked"})
_CAPSULE_ALGORITHMS = frozenset({"AES-256-GCM", "ChaCha20-Poly1305"})


# ─── persist_restore_request ──────────────────────────────────────────────────

def persist_restore_request(
    owner_id: str,
    scope: list[str],
    reason: str,
    idempotency_key: str,
) -> str | None:
    """Persist an explicit context restore request (user-triggered only).

    Fails closed:
      - owner_id or reason empty → None
      - scope empty → None
      - no DB → None
      - idempotency_key empty → None

    ON CONFLICT on idempotency_key returns the existing request ID (idempotent).
    Returns the restore request ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not reason.strip():
        return None
    if not scope:
        return None
    if not idempotency_key.strip():
        return None

    request = ContextRestoreRequest(
        id=f"CREST-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        requested_by_user=True,
        scope=tuple(scope),
        reason=reason,
    )
    boundary = PrivacyBoundary(
        data_class="user_content",
        owner_id=owner_id,
        retention="explicitly_saved",
        cross_feature=False,
    )
    decision = authorize_restore(request, boundary)
    if not decision.allowed:
        return None

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO life_restore_requests"
                "(id, owner_id, scope, reason, requested_by_user, idempotency_key) "
                "VALUES (%s, %s, %s::jsonb, %s, TRUE, %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING RETURNING id",
                (
                    request.id, owner_id,
                    json.dumps(list(scope)),
                    reason[:2000],
                    idempotency_key,
                ),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT id FROM life_restore_requests WHERE idempotency_key = %s AND owner_id = %s",
                    (idempotency_key, owner_id),
                )
                row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_consent_event ────────────────────────────────────────────────────

def persist_consent_event(
    owner_id: str,
    feature_scope: str,
    action: str,
    idempotency_key: str,
) -> str | None:
    """Persist a consent grant or revocation event (append-only).

    Invariants:
      - action must be 'granted' or 'revoked'
      - Consent events are never deleted or updated — revocation adds a new row
      - owner_id and feature_scope must be non-empty

    Returns event ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not feature_scope.strip():
        return None
    if action not in _CONSENT_ACTIONS:
        return None
    if not idempotency_key.strip():
        return None

    event_id = f"LCONSENT-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO life_consent_events"
                "(id, owner_id, feature_scope, action, idempotency_key) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING RETURNING id",
                (event_id, owner_id, feature_scope[:200], action, idempotency_key),
            )
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    "SELECT id FROM life_consent_events WHERE idempotency_key = %s AND owner_id = %s",
                    (idempotency_key, owner_id),
                )
                row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None


# ─── persist_capsule_ref ──────────────────────────────────────────────────────

def persist_capsule_ref(
    owner_id: str,
    ciphertext_ref: str,
    algorithm: str,
    exportable: bool = True,
) -> str | None:
    """Persist an EncryptedCapsuleRef — metadata only, never ciphertext.

    Invariants:
      - ciphertext_ref is a reference/URI — the actual ciphertext is NEVER stored here
      - algorithm must be a known safe algorithm
      - owner_id and ciphertext_ref must be non-empty

    Returns capsule ref ID or None on failure.
    """
    db = store.database
    if db is None:
        return None
    if not owner_id.strip() or not ciphertext_ref.strip():
        return None
    if algorithm not in _CAPSULE_ALGORITHMS:
        return None

    capsule = EncryptedCapsuleRef(
        id=f"ECAP-{uuid4().hex[:8].upper()}",
        owner_id=owner_id,
        ciphertext_ref=ciphertext_ref,
        algorithm=algorithm,
        exportable=exportable,
    )
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO life_capsule_refs"
                "(id, owner_id, ciphertext_ref, algorithm, exportable) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (capsule.id, owner_id, ciphertext_ref[:2000], algorithm, exportable),
            )
            row = cur.fetchone()
        conn.commit()
    return row["id"] if row else None
