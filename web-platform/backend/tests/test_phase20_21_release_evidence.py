"""Tests for Phase 20/21 — Release Evidence and Operational Readiness runtime.

Psycopg and psycopg_pool are stubbed — no real DB required.
Coverage: persist_gate_evidence, persist_recovery_drill,
          evaluate_release_checklist, persist_release_decision.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch


# ─── psycopg stub (must be first) ────────────────────────────────────────────

def _mock_mod(name: str) -> MagicMock:
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()
    return sys.modules[name]


for _mod_name in (
    "psycopg", "psycopg.rows", "psycopg.types", "psycopg.types.json", "psycopg_pool"
):
    _mock_mod(_mod_name)

sys.modules["psycopg.rows"].dict_row = None
sys.modules["psycopg.types.json"].Jsonb = MagicMock
sys.modules["psycopg_pool"].ConnectionPool = MagicMock

# ─── now import app code ──────────────────────────────────────────────────────

import pytest
from app.services.release_evidence_service import (
    persist_gate_evidence,
    persist_recovery_drill,
    evaluate_release_checklist,
    persist_release_decision,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

OWNER = "owner-ph20-test"


def _make_db(row: dict | None = None, rows: list | None = None):
    """Return a mock DB whose cursor returns configured row(s)."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchone.return_value = row
    cur.fetchall.return_value = rows if rows is not None else ([row] if row else [])

    conn = MagicMock()
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cur

    db = MagicMock()
    db.connect.return_value = conn
    return db


def _patch_db(db):
    return patch("app.services.release_evidence_service.store", database=db)


# ─── persist_gate_evidence tests ─────────────────────────────────────────────

_UNSET = object()  # sentinel — distinguishes "not provided" from explicit None


class TestPersistGateEvidence:

    def _call(self, owner_id=OWNER, gate_id="gate-smoke", status="pass",
              evidence_ref=_UNSET, observed_at=None, db=None):
        # Use sentinel: if caller doesn't pass evidence_ref, default to a valid ref
        _evidence_ref = "s3://evidence/1" if evidence_ref is _UNSET else evidence_ref
        _db = _make_db({"id": "GEVID-ABCD"}) if db is None else db
        with _patch_db(_db):
            return persist_gate_evidence(
                owner_id=owner_id,
                gate_id=gate_id,
                status=status,
                evidence_ref=_evidence_ref,
                observed_at=observed_at,
            )

    def test_returns_id_on_success(self):
        assert self._call() == "GEVID-ABCD"

    def test_returns_none_when_db_is_none(self):
        with patch("app.services.release_evidence_service.store", database=None):
            assert persist_gate_evidence(OWNER, "g1", "pass", "ref") is None

    def test_returns_none_for_empty_owner(self):
        assert self._call(owner_id="  ") is None

    def test_returns_none_for_empty_gate_id(self):
        assert self._call(gate_id="  ") is None

    def test_returns_none_for_invalid_status(self):
        assert self._call(status="approved") is None
        assert self._call(status="unknown") is None

    def test_all_valid_statuses(self):
        for st in ("pending", "fail", "blocked"):
            # Non-pass statuses don't require evidence_ref
            result = self._call(status=st, evidence_ref="")
            assert result == "GEVID-ABCD"

    def test_pass_status_requires_evidence_ref(self):
        # Empty evidence_ref with pass status → fail-closed
        assert self._call(status="pass", evidence_ref="") is None
        assert self._call(status="pass", evidence_ref="  ") is None
        assert self._call(status="pass", evidence_ref=None) is None

    def test_pass_status_with_evidence_ref_succeeds(self):
        assert self._call(status="pass", evidence_ref="s3://bucket/evidence.json") == "GEVID-ABCD"

    def test_pending_without_evidence_ref_succeeds(self):
        assert self._call(status="pending", evidence_ref=None) == "GEVID-ABCD"

    def test_returns_none_when_fetchone_returns_none(self):
        db = _make_db(None)
        assert self._call(db=db) is None

    def test_with_observed_at(self):
        assert self._call(observed_at="2026-10-14T00:00:00Z") == "GEVID-ABCD"


# ─── persist_recovery_drill tests ─────────────────────────────────────────────

class TestPersistRecoveryDrill:

    def _call(self, owner_id=OWNER, drill_id="drill-001", kind="backup_restore",
              observed=True, recovered=True, evidence_ref=_UNSET, db=None):
        _evidence_ref = "s3://drill/evidence.json" if evidence_ref is _UNSET else evidence_ref
        _db = _make_db({"id": "DRILL-ABCD"}) if db is None else db
        with _patch_db(_db):
            return persist_recovery_drill(
                owner_id=owner_id,
                drill_id=drill_id,
                kind=kind,
                observed=observed,
                recovered=recovered,
                evidence_ref=_evidence_ref,
            )

    def test_returns_id_on_success(self):
        assert self._call() == "DRILL-ABCD"

    def test_returns_none_when_db_is_none(self):
        with patch("app.services.release_evidence_service.store", database=None):
            assert persist_recovery_drill(OWNER, "d1", "rollback", True, True, "ref") is None

    def test_returns_none_for_empty_owner(self):
        assert self._call(owner_id="  ") is None

    def test_returns_none_for_empty_drill_id(self):
        assert self._call(drill_id="  ") is None

    def test_returns_none_for_invalid_kind(self):
        assert self._call(kind="chaos_test") is None
        assert self._call(kind="") is None

    def test_all_valid_kinds(self):
        for kind in ("backup_restore", "rollback", "failover"):
            assert self._call(kind=kind) == "DRILL-ABCD"

    def test_returns_none_when_not_observed(self):
        # recovery_is_evidenced requires observed=True
        assert self._call(observed=False, recovered=True) is None

    def test_returns_none_when_not_recovered(self):
        assert self._call(observed=True, recovered=False) is None

    def test_returns_none_when_evidence_ref_missing(self):
        # recovery_is_evidenced requires non-empty evidence_ref
        assert self._call(evidence_ref=None) is None
        assert self._call(evidence_ref="") is None

    def test_returns_none_when_fetchone_returns_none(self):
        db = _make_db(None)
        assert self._call(db=db) is None


# ─── evaluate_release_checklist tests ────────────────────────────────────────

class TestEvaluateReleaseChecklist:

    def _call(self, owner_id=OWNER, revision="v1.0", required_gates=None, db=None, rows=None):
        _gates = ["gate-smoke", "gate-db"] if required_gates is None else required_gates
        _rows = rows
        if _rows is None:
            _rows = [
                {"gate_id": "gate-smoke", "status": "pass",
                 "evidence_ref": "ref-1", "observed_at": None},
                {"gate_id": "gate-db", "status": "pass",
                 "evidence_ref": "ref-2", "observed_at": None},
            ]
        _db = _make_db(rows=_rows) if db is None else db
        with _patch_db(_db):
            return evaluate_release_checklist(
                owner_id=owner_id,
                revision=revision,
                required_gates=_gates,
            )

    def test_returns_pass_when_all_gates_pass(self):
        result = self._call()
        assert result is not None
        assert result["status"] == "pass"
        assert result["revision"] == "v1.0"

    def test_returns_none_when_db_is_none(self):
        with patch("app.services.release_evidence_service.store", database=None):
            assert evaluate_release_checklist(OWNER, "v1", ["gate-1"]) is None

    def test_returns_none_for_empty_owner(self):
        assert self._call(owner_id="  ") is None

    def test_returns_none_for_empty_revision(self):
        assert self._call(revision="  ") is None

    def test_returns_none_for_empty_required_gates(self):
        # sentinel: empty list → None (not default)
        _gates = []
        with _make_db(rows=[]) as _: pass  # just verify sentinel
        assert self._call(required_gates=_gates) is None

    def test_returns_pending_when_gate_missing(self):
        rows = [
            {"gate_id": "gate-smoke", "status": "pass",
             "evidence_ref": "ref-1", "observed_at": None},
            # gate-db is missing
        ]
        result = self._call(rows=rows)
        assert result["status"] == "pending"

    def test_returns_fail_when_gate_not_pass(self):
        rows = [
            {"gate_id": "gate-smoke", "status": "fail",
             "evidence_ref": "ref-1", "observed_at": None},
            {"gate_id": "gate-db", "status": "pass",
             "evidence_ref": "ref-2", "observed_at": None},
        ]
        result = self._call(rows=rows)
        assert result["status"] == "fail"

    def test_returns_fail_when_evidence_ref_missing_on_pass(self):
        rows = [
            {"gate_id": "gate-smoke", "status": "pass",
             "evidence_ref": None, "observed_at": None},  # pass without ref → fail
            {"gate_id": "gate-db", "status": "pass",
             "evidence_ref": "ref-2", "observed_at": None},
        ]
        result = self._call(rows=rows)
        assert result["status"] == "fail"

    def test_result_contains_evidence_list(self):
        result = self._call()
        assert "evidence" in result
        assert isinstance(result["evidence"], list)

    def test_result_contains_required_gates(self):
        result = self._call()
        assert "required_gates" in result

    def test_deduplicates_gate_rows_using_latest_first(self):
        # Two rows for same gate_id — latest (first in DESC) wins
        rows = [
            {"gate_id": "gate-smoke", "status": "pass",
             "evidence_ref": "new-ref", "observed_at": None},
            {"gate_id": "gate-smoke", "status": "fail",
             "evidence_ref": "old-ref", "observed_at": None},
            {"gate_id": "gate-db", "status": "pass",
             "evidence_ref": "ref-2", "observed_at": None},
        ]
        result = self._call(rows=rows)
        assert result["status"] == "pass"


# ─── persist_release_decision tests ──────────────────────────────────────────

class TestPersistReleaseDecision:

    def _call(self, owner_id=OWNER, revision="v1.0", approved=True,
              evidence=None, db=None):
        _evidence = evidence if evidence is not None else [
            {"gate_id": "g1", "status": "pass", "evidence_ref": "ref-1"}
        ]
        _db = _make_db({"id": "RDEC-ABCD"}) if db is None else db
        with _patch_db(_db):
            return persist_release_decision(
                owner_id=owner_id,
                revision=revision,
                approved=approved,
                evidence=_evidence,
            )

    def test_returns_id_on_success(self):
        assert self._call() == "RDEC-ABCD"

    def test_returns_none_when_db_is_none(self):
        with patch("app.services.release_evidence_service.store", database=None):
            assert persist_release_decision(OWNER, "v1", True, [{"g": 1}]) is None

    def test_returns_none_for_empty_owner(self):
        assert self._call(owner_id="  ") is None

    def test_returns_none_for_empty_revision(self):
        assert self._call(revision="  ") is None

    def test_returns_none_for_empty_evidence_list(self):
        # sentinel: [] is a distinct value from None default
        assert self._call(evidence=[]) is None

    def test_approved_false_is_allowed(self):
        # Unapproved decisions can still be recorded
        assert self._call(approved=False) == "RDEC-ABCD"

    def test_returns_none_when_fetchone_returns_none(self):
        db = _make_db(None)
        assert self._call(db=db) is None

    def test_multi_evidence_items(self):
        evidence = [
            {"gate_id": "g1", "status": "pass"},
            {"gate_id": "g2", "status": "pass"},
            {"gate_id": "g3", "status": "fail"},
        ]
        assert self._call(evidence=evidence) == "RDEC-ABCD"
