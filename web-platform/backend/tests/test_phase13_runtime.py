from __future__ import annotations

"""Phase 13 — AI Active Layer runtime integration tests.

Tests cover:
- EvidenceRef and Finding contract construction
- Lifecycle event validation and terminal fencing
- decide_execution routing logic (start / resume / retry / ignore / reject)
- build_evidence_refs chunk-to-contract conversion (mocked DB)
- persist_lifecycle_event idempotency and fencing (no-DB path)
- persist_decision_record evidence-required invariant (no-DB path)
- finding_ready_for_review gate
- decision_has_evidence gate
"""

import sys
import types
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# ─── Stub out psycopg and all DB-layer modules at collection time ─────────────
# This lets us test pure-Python active_layer contracts and agent helpers
# without requiring a database installation in local dev or isolated test runs.
# CI has psycopg installed via requirements.lock and will run the full suite.
from unittest.mock import MagicMock

def _mock_mod(name: str) -> MagicMock:
    """Create a MagicMock module and register it (and parent packages) in sys.modules."""
    parts = name.split(".")
    # Register each ancestor package if not already present.
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()
    return sys.modules[name]  # type: ignore[return-value]

# Register the full psycopg tree before any app import triggers it.
for _mod_name in (
    "psycopg",
    "psycopg.rows",
    "psycopg.types",
    "psycopg.types.json",
    "psycopg_pool",
):
    _mock_mod(_mod_name)

# Pin specific attributes that are imported by name in persistence.py / store.py
sys.modules["psycopg.rows"].dict_row = None  # type: ignore[attr-defined]
sys.modules["psycopg.types.json"].Jsonb = MagicMock  # type: ignore[attr-defined]

_fake_pool_cls = MagicMock
sys.modules["psycopg_pool"].ConnectionPool = _fake_pool_cls  # type: ignore[attr-defined]

from app.services.active_layer import (
    EvidenceRef,
    Finding,
    AgentRun,
    DecisionRecord,
    AgentLifecycleEvent,
    AgentStatus,
    lifecycle_event_is_valid,
    terminal_event_is_fenced,
    decide_execution,
    ExecutionLease,
    ExecutionDecision,
    finding_ready_for_review,
    decision_has_evidence,
)
from app.services.agent import (
    build_evidence_refs,
    persist_lifecycle_event,
    persist_decision_record,
)


# ─── Contracts ────────────────────────────────────────────────────────────────

class TestEvidenceRef:
    def test_minimal_construction(self):
        ref = EvidenceRef(source_type="chunk", source_id="C-001")
        assert ref.source_type == "chunk"
        assert ref.source_id == "C-001"
        assert ref.locator is None
        assert ref.excerpt is None

    def test_full_construction(self):
        ref = EvidenceRef("book", "B-001", locator="page=5", excerpt="Key sentence.")
        assert ref.locator == "page=5"
        assert ref.excerpt == "Key sentence."

    def test_frozen(self):
        ref = EvidenceRef("chunk", "C-001")
        with pytest.raises((AttributeError, TypeError)):
            ref.source_id = "C-002"  # type: ignore[misc]


class TestFinding:
    def test_default_review_state_is_draft(self):
        f = Finding(id="F-001", statement="Test statement")
        assert f.review_state == "draft"
        assert f.evidence == ()

    def test_with_evidence(self):
        ev = EvidenceRef("chunk", "C-001")
        f = Finding(id="F-002", statement="Claim", evidence=(ev,), confidence=0.9)
        assert len(f.evidence) == 1
        assert f.confidence == 0.9

    def test_finding_ready_for_review_requires_evidence_and_non_draft(self):
        ev = EvidenceRef("chunk", "C-001")
        # draft → not ready
        draft = Finding("F-1", "stmt", evidence=(ev,), review_state="draft")
        assert not finding_ready_for_review(draft)
        # needs_review without evidence → not ready
        no_ev = Finding("F-2", "stmt", evidence=(), review_state="needs_review")
        assert not finding_ready_for_review(no_ev)
        # needs_review + evidence → ready
        ready = Finding("F-3", "stmt", evidence=(ev,), review_state="needs_review")
        assert finding_ready_for_review(ready)
        # empty statement → not ready
        empty = Finding("F-4", "", evidence=(ev,), review_state="needs_review")
        assert not finding_ready_for_review(empty)


class TestDecisionRecord:
    def test_decision_has_evidence_requires_all_fields(self):
        ev = EvidenceRef("chunk", "C-001")
        ok = DecisionRecord("D-1", "Use approach A", "Cheaper and faster", evidence=(ev,))
        assert decision_has_evidence(ok)

    def test_no_evidence_fails(self):
        bad = DecisionRecord("D-2", "Use approach B", "Good idea", evidence=())
        assert not decision_has_evidence(bad)

    def test_empty_decision_fails(self):
        ev = EvidenceRef("chunk", "C-001")
        bad = DecisionRecord("D-3", "", "Rationale", evidence=(ev,))
        assert not decision_has_evidence(bad)


# ─── Lifecycle Events ─────────────────────────────────────────────────────────

class TestLifecycleEvents:
    def _event(self, run_id="R-1", owner_id="owner", event_type="started", idem_key="k1"):
        return AgentLifecycleEvent(
            run_id=run_id,
            owner_id=owner_id,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            idempotency_key=idem_key,
        )

    def test_valid_event(self):
        assert lifecycle_event_is_valid(self._event())

    def test_empty_run_id_invalid(self):
        assert not lifecycle_event_is_valid(self._event(run_id=""))

    def test_empty_owner_id_invalid(self):
        assert not lifecycle_event_is_valid(self._event(owner_id=""))

    def test_empty_idempotency_key_invalid(self):
        assert not lifecycle_event_is_valid(self._event(idem_key=""))

    def test_terminal_fencing_rejects_non_terminal_on_completed(self):
        assert terminal_event_is_fenced("completed", "started")
        assert terminal_event_is_fenced("failed", "resumed")
        assert terminal_event_is_fenced("cancelled", "retry_scheduled")

    def test_terminal_fencing_allows_terminal_on_terminal(self):
        # Terminal → terminal is not fenced (already done)
        assert not terminal_event_is_fenced("completed", "completed")
        assert not terminal_event_is_fenced("failed", "failed")

    def test_non_terminal_not_fenced(self):
        assert not terminal_event_is_fenced("queued", "started")
        assert not terminal_event_is_fenced("running", "paused")


# ─── Execution Decisions ──────────────────────────────────────────────────────

class TestDecideExecution:
    def test_queued_started_not_seen_starts(self):
        d = decide_execution("queued", "started", False)
        assert d.action == "start"

    def test_running_started_seen_ignores_duplicate(self):
        d = decide_execution("running", "started", True)
        assert d.action == "ignore"

    def test_completed_retry_rejects(self):
        d = decide_execution("completed", "retry_scheduled", False)
        assert d.action == "reject"

    def test_failed_retry_rejects(self):
        d = decide_execution("failed", "started", False)
        assert d.action == "reject"

    def test_paused_resumed_resumes(self):
        d = decide_execution("paused", "resumed", False)
        assert d.action == "resume"

    def test_retry_scheduled_retries(self):
        d = decide_execution("queued", "retry_scheduled", False)
        assert d.action == "retry"

    def test_execution_lease_shape(self):
        lease = ExecutionLease(
            run_id="R-1",
            owner_id="owner",
            lease_id="L-1",
            attempt=2,
            heartbeat_at="2026-01-01T00:00:00Z",
            expires_at="2026-01-01T00:05:00Z",
        )
        assert lease.attempt == 2
        assert lease.run_id == "R-1"


# ─── build_evidence_refs ──────────────────────────────────────────────────────

class TestBuildEvidenceRefs:
    def test_converts_chunk_rows(self):
        rows = [
            {"id": "C-001", "content": "Hello world", "page_number": 1},
            {"id": "C-002", "content": "Second chunk", "page_number": None},
        ]
        refs = build_evidence_refs(rows)
        assert len(refs) == 2
        assert refs[0]["source_type"] == "chunk"
        assert refs[0]["source_id"] == "C-001"
        assert refs[0]["locator"] == "page=1"
        assert refs[0]["excerpt"] == "Hello world"
        assert refs[1]["locator"] is None

    def test_empty_rows_returns_empty(self):
        assert build_evidence_refs([]) == []

    def test_long_content_truncated(self):
        long_content = "x" * 500
        refs = build_evidence_refs([{"id": "C-001", "content": long_content, "page_number": None}])
        assert len(refs[0]["excerpt"]) <= 200

    def test_missing_fields_safe(self):
        refs = build_evidence_refs([{}])
        assert refs[0]["source_id"] == ""
        assert refs[0]["locator"] is None
        assert refs[0]["excerpt"] is None


# ─── persist_lifecycle_event (no-DB path) ─────────────────────────────────────

class TestPersistLifecycleEventNoDB:
    def test_returns_false_when_no_database(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = None
            result = persist_lifecycle_event("R-1", "J-1", "owner", "started", "k1")
        assert result is False

    def test_invalid_event_returns_false(self):
        """Empty run_id fails lifecycle_event_is_valid."""
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = MagicMock()
            result = persist_lifecycle_event("", "J-1", "owner", "started", "k1")
        assert result is False

    def test_empty_idempotency_key_returns_false(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = MagicMock()
            result = persist_lifecycle_event("R-1", "J-1", "owner", "started", "")
        assert result is False


# ─── persist_decision_record (no-DB path) ────────────────────────────────────

class TestPersistDecisionRecordNoDB:
    def test_returns_none_when_no_database(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = None
            result = persist_decision_record("J-1", "owner", "decision", "rationale", [{"source_type": "chunk"}])
        assert result is None

    def test_returns_none_when_no_evidence(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = MagicMock()
            result = persist_decision_record("J-1", "owner", "decision", "rationale", [])
        assert result is None

    def test_returns_none_when_empty_decision(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = MagicMock()
            result = persist_decision_record("J-1", "owner", "", "rationale", [{"source_type": "chunk"}])
        assert result is None

    def test_returns_none_when_empty_rationale(self):
        with patch("app.services.agent.store") as mock_store:
            mock_store.database = MagicMock()
            result = persist_decision_record("J-1", "owner", "decision", "", [{"source_type": "chunk"}])
        assert result is None
