from __future__ import annotations

"""Phase 17 — Cognix Core Integration runtime tests.

Tests cover:
- EvidenceBoundArtifact contract + ready_for_human_review gate
- DocumentClassification + classification_is_valid
- lifecycle_transition_allowed state machine
- ParallelText + parallel_text_is_valid
- TutorCorrection / TutorGoal construction
- persist_evidence_artifact() — evidence required, type allowlist (no-DB)
- persist_document_classification() — confidence validation (no-DB)
- apply_document_lifecycle_transition() — state machine check (no-DB)
- persist_parallel_text() — language pair validation (no-DB)
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

# ─── Stub psycopg tree ────────────────────────────────────────────────────────

def _mock_mod(name: str) -> MagicMock:
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()
    return sys.modules[name]  # type: ignore[return-value]

for _mod_name in (
    "psycopg", "psycopg.rows", "psycopg.types", "psycopg.types.json", "psycopg_pool",
):
    _mock_mod(_mod_name)

sys.modules["psycopg.rows"].dict_row = None  # type: ignore[attr-defined]
sys.modules["psycopg.types.json"].Jsonb = MagicMock  # type: ignore[attr-defined]
sys.modules["psycopg_pool"].ConnectionPool = MagicMock  # type: ignore[attr-defined]

from app.services.core_integration import (
    EvidenceBoundArtifact,
    ready_for_human_review,
    DocumentClassification,
    OCRReview,
    classification_is_valid,
    lifecycle_transition_allowed,
    ParallelText,
    TutorCorrection,
    TutorGoal,
    parallel_text_is_valid,
)
from app.services.active_layer.contracts import EvidenceRef
from app.services.core_integration_service import (
    persist_evidence_artifact,
    persist_document_classification,
    apply_document_lifecycle_transition,
    persist_parallel_text,
)


# ─── EvidenceBoundArtifact ────────────────────────────────────────────────────

class TestEvidenceBoundArtifact:
    def _ev(self) -> EvidenceRef:
        return EvidenceRef("chunk", "C-001")

    def test_ready_requires_evidence_and_needs_review_state(self):
        ev = self._ev()
        ready = EvidenceBoundArtifact("A-1", "claim", "owner", evidence=(ev,), review_state="needs_review")
        assert ready_for_human_review(ready)

    def test_draft_not_ready(self):
        ev = self._ev()
        draft = EvidenceBoundArtifact("A-2", "claim", "owner", evidence=(ev,), review_state="draft")
        assert not ready_for_human_review(draft)

    def test_no_evidence_not_ready(self):
        no_ev = EvidenceBoundArtifact("A-3", "claim", "owner", evidence=(), review_state="needs_review")
        assert not ready_for_human_review(no_ev)

    def test_empty_owner_not_ready(self):
        ev = self._ev()
        no_owner = EvidenceBoundArtifact("A-4", "claim", "", evidence=(ev,), review_state="needs_review")
        assert not ready_for_human_review(no_owner)

    def test_frozen(self):
        a = EvidenceBoundArtifact("A-5", "claim", "owner")
        with pytest.raises((AttributeError, TypeError)):
            a.review_state = "approved"  # type: ignore[misc]


# ─── DocumentClassification ───────────────────────────────────────────────────

class TestDocumentClassification:
    def test_valid_confidence(self):
        dc = DocumentClassification("contract", 0.92)
        assert classification_is_valid(dc)

    def test_zero_confidence_valid(self):
        dc = DocumentClassification("letter", 0.0)
        assert classification_is_valid(dc)

    def test_one_confidence_valid(self):
        dc = DocumentClassification("form", 1.0)
        assert classification_is_valid(dc)

    def test_above_one_invalid(self):
        dc = DocumentClassification("invoice", 1.01)
        assert not classification_is_valid(dc)

    def test_below_zero_invalid(self):
        dc = DocumentClassification("receipt", -0.01)
        assert not classification_is_valid(dc)


# ─── lifecycle_transition_allowed ─────────────────────────────────────────────

class TestLifecycleTransition:
    def test_inbox_to_processing_allowed(self):
        assert lifecycle_transition_allowed("inbox", "processing")

    def test_processing_to_review_allowed(self):
        assert lifecycle_transition_allowed("processing", "review")

    def test_review_to_approved_allowed(self):
        assert lifecycle_transition_allowed("review", "approved")

    def test_review_to_processing_allowed(self):
        assert lifecycle_transition_allowed("review", "processing")

    def test_approved_to_indexed_allowed(self):
        assert lifecycle_transition_allowed("approved", "indexed")

    def test_indexed_to_archived_allowed(self):
        assert lifecycle_transition_allowed("indexed", "archived")

    def test_inbox_to_approved_not_allowed(self):
        assert not lifecycle_transition_allowed("inbox", "approved")

    def test_approved_to_inbox_not_allowed(self):
        assert not lifecycle_transition_allowed("approved", "inbox")

    def test_deleted_has_no_transitions(self):
        assert not lifecycle_transition_allowed("deleted", "archived")


# ─── ParallelText ─────────────────────────────────────────────────────────────

class TestParallelText:
    def test_valid(self):
        pt = ParallelText("my", "ja", "ကျွန်တော်", "私", reading="わたし")
        assert parallel_text_is_valid(pt)

    def test_same_language_invalid(self):
        pt = ParallelText("my", "my", "ကျွန်တော်", "ကျွန်တော်")
        assert not parallel_text_is_valid(pt)

    def test_empty_source_invalid(self):
        pt = ParallelText("my", "ja", "", "私")
        assert not parallel_text_is_valid(pt)

    def test_empty_translation_invalid(self):
        pt = ParallelText("my", "ja", "ကျွန်တော်", "")
        assert not parallel_text_is_valid(pt)

    def test_frozen(self):
        pt = ParallelText("my", "ja", "src", "trans")
        with pytest.raises((AttributeError, TypeError)):
            pt.source = "changed"  # type: ignore[misc]


# ─── TutorGoal ────────────────────────────────────────────────────────────────

class TestTutorGoal:
    def test_construction(self):
        g = TutorGoal("JLPT", "N3")
        assert g.framework == "JLPT"
        assert g.level == "N3"

    def test_frozen(self):
        g = TutorGoal("CEFR", "B2")
        with pytest.raises((AttributeError, TypeError)):
            g.level = "C1"  # type: ignore[misc]


# ─── persist_evidence_artifact (no-DB) ───────────────────────────────────────

class TestPersistEvidenceArtifactNoDB:
    _EV = [{"source_type": "chunk", "source_id": "C-001"}]

    def _call(self, owner="owner", atype="claim", refs=None, db=None):
        _refs = self._EV if refs is None else refs
        with patch("app.services.core_integration_service.store") as m:
            m.database = db
            return persist_evidence_artifact(owner, atype, _refs, {})

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_unknown_type(self):
        assert self._call(atype="unknown_type", db=MagicMock()) is None

    def test_none_when_no_evidence(self):
        assert self._call(refs=[], db=MagicMock()) is None


# ─── persist_document_classification (no-DB) ─────────────────────────────────

class TestPersistDocumentClassificationNoDB:
    def _call(self, owner="owner", doc_id="DOC-1", dtype="contract", confidence=0.9, db=None):
        with patch("app.services.core_integration_service.store") as m:
            m.database = db
            return persist_document_classification(owner, doc_id, dtype, confidence)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_invalid_confidence(self):
        assert self._call(confidence=1.5, db=MagicMock()) is None

    def test_none_when_negative_confidence(self):
        assert self._call(confidence=-0.1, db=MagicMock()) is None


# ─── apply_document_lifecycle_transition (no-DB) ─────────────────────────────

class TestApplyLifecycleTransitionNoDB:
    def _call(self, owner="owner", doc_id="D-1", current="inbox", target="processing", db=None):
        with patch("app.services.core_integration_service.store") as m:
            m.database = db
            return apply_document_lifecycle_transition(owner, doc_id, current, target)

    def test_false_when_no_db(self):
        assert self._call(db=None) is False

    def test_false_when_disallowed_transition(self):
        assert self._call(current="inbox", target="approved", db=MagicMock()) is False

    def test_false_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is False


# ─── persist_parallel_text (no-DB) ────────────────────────────────────────────

class TestPersistParallelTextNoDB:
    def _call(self, owner="owner", src_lang="my", tgt_lang="ja", source="src", trans="trans", db=None):
        with patch("app.services.core_integration_service.store") as m:
            m.database = db
            return persist_parallel_text(owner, src_lang, tgt_lang, source, trans)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_same_language(self):
        assert self._call(src_lang="my", tgt_lang="my", db=MagicMock()) is None

    def test_none_when_empty_source(self):
        assert self._call(source="", db=MagicMock()) is None

    def test_none_when_empty_translation(self):
        assert self._call(trans="", db=MagicMock()) is None
