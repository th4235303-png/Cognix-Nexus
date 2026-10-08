import unittest

from app.services.active_layer.contracts import DecisionRecord, EvidenceRef, Finding
from app.services.active_layer.validation import decision_has_evidence, finding_ready_for_review

class ActiveLayerValidationTests(unittest.TestCase):
    def test_finding_requires_evidence_and_non_draft_review_state(self):
        evidence = EvidenceRef(source_type="book", source_id="b1")
        self.assertFalse(finding_ready_for_review(Finding(id="f", statement="claim")))
        self.assertTrue(finding_ready_for_review(Finding(id="f", statement="claim", evidence=(evidence,), review_state="needs_review")))

    def test_decision_requires_evidence(self):
        decision = DecisionRecord(id="d", decision="use", rationale="supported", evidence=())
        self.assertFalse(decision_has_evidence(decision))
        decision = DecisionRecord(id="d", decision="use", rationale="supported", evidence=(EvidenceRef("book", "b1"),))
        self.assertTrue(decision_has_evidence(decision))

if __name__ == "__main__":
    unittest.main()
