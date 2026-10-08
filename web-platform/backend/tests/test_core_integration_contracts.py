import unittest

from app.services.active_layer.contracts import EvidenceRef
from app.services.core_integration.contracts import (
    EvidenceBoundArtifact,
    ready_for_human_review,
)


class CoreIntegrationContractTests(unittest.TestCase):
    def test_review_ready_requires_owner_evidence_and_state(self):
        evidence = EvidenceRef(
            source_type="chunk",
            source_id="chunk-1",
            locator="page:1",
            excerpt_hash="hash-1",
        )
        artifact = EvidenceBoundArtifact(
            id="artifact-1",
            artifact_type="research_report",
            owner_id="owner-1",
            evidence=(evidence,),
            review_state="needs_review",
        )
        self.assertTrue(ready_for_human_review(artifact))

    def test_ownerless_artifact_fails_closed(self):
        evidence = EvidenceRef(
            source_type="chunk",
            source_id="chunk-1",
            locator="page:1",
            excerpt_hash="hash-1",
        )
        artifact = EvidenceBoundArtifact(
            id="artifact-1",
            artifact_type="claim",
            owner_id="",
            evidence=(evidence,),
            review_state="needs_review",
        )
        self.assertFalse(ready_for_human_review(artifact))

    def test_evidence_less_artifact_fails_closed(self):
        artifact = EvidenceBoundArtifact(
            id="artifact-1",
            artifact_type="claim",
            owner_id="owner-1",
            evidence=(),
            review_state="needs_review",
        )
        self.assertFalse(ready_for_human_review(artifact))

    def test_draft_artifact_fails_closed(self):
        evidence = EvidenceRef(
            source_type="chunk",
            source_id="chunk-1",
            locator="page:1",
            excerpt_hash="hash-1",
        )
        artifact = EvidenceBoundArtifact(
            id="artifact-1",
            artifact_type="claim",
            owner_id="owner-1",
            evidence=(evidence,),
            review_state="draft",
        )
        self.assertFalse(ready_for_human_review(artifact))


if __name__ == "__main__":
    unittest.main()
