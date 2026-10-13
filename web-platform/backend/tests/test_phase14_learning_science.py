from __future__ import annotations

"""Phase 14 — Learning Science runtime integration tests.

Tests cover:
- LearningSignal and LearningPathItem contract construction
- decay_weight() deterministic invariants
- LearningCandidate priority() calculation
- build_path() ranking logic
- persist_learning_signal() validation (no-DB path)
- persist_learning_path() validation (no-DB path)
- build_path_from_db() no-DB path
"""

import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# ─── Stub out psycopg and all DB-layer modules at collection time ─────────────
# Same pattern as test_phase13_runtime.py — allows local runs without psycopg.

def _mock_mod(name: str) -> MagicMock:
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()
    return sys.modules[name]  # type: ignore[return-value]

for _mod_name in (
    "psycopg",
    "psycopg.rows",
    "psycopg.types",
    "psycopg.types.json",
    "psycopg_pool",
):
    _mock_mod(_mod_name)

sys.modules["psycopg.rows"].dict_row = None  # type: ignore[attr-defined]
sys.modules["psycopg.types.json"].Jsonb = MagicMock  # type: ignore[attr-defined]
sys.modules["psycopg_pool"].ConnectionPool = MagicMock  # type: ignore[attr-defined]

from app.services.learning_science import (
    LearningSignal,
    LearningPathItem,
    LearningCandidate,
    decay_weight,
    priority,
    build_path,
)
from app.services.learning_science_service import (
    persist_learning_signal,
    persist_learning_path,
    build_path_from_db,
)


# ─── decay_weight ─────────────────────────────────────────────────────────────

class TestDecayWeight:
    def test_zero_age_returns_one(self):
        assert decay_weight(0.0, 14.0) == pytest.approx(1.0)

    def test_half_life_returns_half(self):
        assert decay_weight(14.0, 14.0) == pytest.approx(0.5)

    def test_double_half_life_returns_quarter(self):
        assert decay_weight(28.0, 14.0) == pytest.approx(0.25)

    def test_negative_age_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            decay_weight(-1.0, 14.0)

    def test_zero_half_life_raises(self):
        with pytest.raises(ValueError, match="positive"):
            decay_weight(0.0, 0.0)

    def test_negative_half_life_raises(self):
        with pytest.raises(ValueError, match="positive"):
            decay_weight(0.0, -1.0)


# ─── LearningSignal ───────────────────────────────────────────────────────────

class TestLearningSignal:
    def test_minimal_construction(self):
        sig = LearningSignal(
            id="LSIG-001",
            subject_id="chapter:5",
            signal_type="recall",
            strength=0.8,
            occurred_at="2026-01-01T00:00:00Z",
        )
        assert sig.strength == 0.8
        assert sig.evidence_refs == ()

    def test_with_evidence(self):
        sig = LearningSignal(
            id="LSIG-002",
            subject_id="chapter:5",
            signal_type="difficulty",
            strength=0.3,
            occurred_at="2026-01-01T00:00:00Z",
            evidence_refs=("C-001", "C-002"),
        )
        assert len(sig.evidence_refs) == 2

    def test_frozen(self):
        sig = LearningSignal("LSIG-003", "ch:1", "review", 0.5, "2026-01-01T00:00:00Z")
        with pytest.raises((AttributeError, TypeError)):
            sig.strength = 0.9  # type: ignore[misc]


# ─── LearningPathItem ─────────────────────────────────────────────────────────

class TestLearningPathItem:
    def test_construction(self):
        item = LearningPathItem(
            id="LPATH-001",
            subject_id="chapter:5",
            position=0,
            reason="weakness×decay priority",
            evidence_refs=("LSIG-001",),
        )
        assert item.position == 0
        assert item.reason == "weakness×decay priority"

    def test_frozen(self):
        item = LearningPathItem("LPATH-002", "ch:1", 0, "reason", ())
        with pytest.raises((AttributeError, TypeError)):
            item.position = 99  # type: ignore[misc]


# ─── priority() ──────────────────────────────────────────────────────────────

class TestPriority:
    def test_zero_age_full_weakness(self):
        c = LearningCandidate("ch:1", weakness=1.0, age_days=0.0, half_life_days=14.0)
        assert priority(c) == pytest.approx(1.0)

    def test_decays_over_time(self):
        c0 = LearningCandidate("ch:1", weakness=1.0, age_days=0.0, half_life_days=14.0)
        c14 = LearningCandidate("ch:1", weakness=1.0, age_days=14.0, half_life_days=14.0)
        assert priority(c0) > priority(c14)

    def test_zero_weakness_always_zero(self):
        c = LearningCandidate("ch:1", weakness=0.0, age_days=0.0, half_life_days=14.0)
        assert priority(c) == pytest.approx(0.0)

    def test_empty_subject_id_raises(self):
        c = LearningCandidate("", weakness=0.5, age_days=0.0, half_life_days=14.0)
        with pytest.raises(ValueError, match="subject_id"):
            priority(c)

    def test_negative_weakness_clamped_to_zero(self):
        c = LearningCandidate("ch:1", weakness=-1.0, age_days=0.0, half_life_days=14.0)
        assert priority(c) == pytest.approx(0.0)


# ─── build_path() ─────────────────────────────────────────────────────────────

class TestBuildPath:
    def _candidate(self, subject_id: str, weakness: float, age_days: float = 0.0) -> LearningCandidate:
        return LearningCandidate(subject_id, weakness=weakness, age_days=age_days, half_life_days=14.0)

    def test_ranks_by_priority_descending(self):
        candidates = (
            self._candidate("ch:A", weakness=0.2),
            self._candidate("ch:B", weakness=0.9),
            self._candidate("ch:C", weakness=0.5),
        )
        path = build_path(candidates, limit=3)
        assert path[0].subject_id == "ch:B"
        assert path[1].subject_id == "ch:C"
        assert path[2].subject_id == "ch:A"

    def test_limit_zero_returns_empty(self):
        candidates = (self._candidate("ch:A", 0.9),)
        assert build_path(candidates, limit=0) == ()

    def test_limit_truncates(self):
        candidates = tuple(self._candidate(f"ch:{i}", weakness=float(i) / 10) for i in range(10))
        path = build_path(candidates, limit=3)
        assert len(path) == 3

    def test_empty_candidates_returns_empty(self):
        assert build_path((), limit=5) == ()

    def test_position_is_zero_indexed(self):
        candidates = (
            self._candidate("ch:A", weakness=0.9),
            self._candidate("ch:B", weakness=0.5),
        )
        path = build_path(candidates, limit=2)
        assert path[0].position == 0
        assert path[1].position == 1


# ─── persist_learning_signal (no-DB path) ────────────────────────────────────

class TestPersistLearningSignalNoDB:
    def test_returns_none_when_no_database(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = None
            result = persist_learning_signal("owner", "ch:1", "recall", 0.8, [{"source_id": "x"}], "idem-1")
        assert result is None

    def test_returns_none_when_no_evidence(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_signal("owner", "ch:1", "recall", 0.8, [], "idem-1")
        assert result is None

    def test_returns_none_when_empty_owner(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_signal("", "ch:1", "recall", 0.8, [{"source_id": "x"}], "idem-1")
        assert result is None

    def test_returns_none_when_invalid_signal_type(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_signal("owner", "ch:1", "invalid_type", 0.8, [{"source_id": "x"}], "idem-1")
        assert result is None

    def test_returns_none_when_strength_out_of_range(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_signal("owner", "ch:1", "recall", 1.5, [{"source_id": "x"}], "idem-1")
        assert result is None

    def test_returns_none_when_empty_idempotency_key(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_signal("owner", "ch:1", "recall", 0.8, [{"source_id": "x"}], "")
        assert result is None


# ─── persist_learning_path (no-DB path) ──────────────────────────────────────

class TestPersistLearningPathNoDB:
    def _item(self, subject_id: str = "ch:1", reason: str = "ok", evidence: tuple = ("E-1",)) -> LearningPathItem:
        return LearningPathItem("x", subject_id, 0, reason, evidence)

    def test_returns_empty_when_no_database(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = None
            result = persist_learning_path("owner", [self._item()])
        assert result == []

    def test_returns_empty_when_empty_owner(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_path("", [self._item()])
        assert result == []

    def test_returns_empty_when_no_items(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = MagicMock()
            result = persist_learning_path("owner", [])
        assert result == []


# ─── build_path_from_db (no-DB path) ─────────────────────────────────────────

class TestBuildPathFromDbNoDB:
    def test_returns_empty_when_no_database(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = None
            result = build_path_from_db("owner")
        assert result == ()

    def test_returns_empty_when_empty_owner(self):
        with patch("app.services.learning_science_service.store") as m:
            m.database = None
            result = build_path_from_db("")
        assert result == ()
