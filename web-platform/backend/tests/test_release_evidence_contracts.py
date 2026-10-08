import unittest

from app.services.release_evidence.contracts import (
    GateEvidence,
    ReleaseDecision,
    release_is_ready,
)


class ReleaseEvidenceContractTests(unittest.TestCase):
    def test_release_requires_approved_revision_and_evidence_backed_passes(self):
        decision = ReleaseDecision(
            revision="main@abc123",
            approved=True,
            required_gate_ids=("ci", "browser"),
            evidence=(
                GateEvidence("ci", "pass", "evidence://ci"),
                GateEvidence("browser", "pass", "evidence://browser"),
            ),
        )
        self.assertTrue(release_is_ready(decision))

    def test_missing_evidence_or_blocked_gate_fails_closed(self):
        decision = ReleaseDecision(
            revision="main@abc123",
            approved=True,
            required_gate_ids=("ci", "browser"),
            evidence=(GateEvidence("ci", "pass", "evidence://ci"),),
        )
        self.assertFalse(release_is_ready(decision))

    def test_unapproved_release_fails_closed(self):
        decision = ReleaseDecision(
            revision="main@abc123",
            approved=False,
            required_gate_ids=("ci",),
            evidence=(GateEvidence("ci", "pass", "evidence://ci"),),
        )
        self.assertFalse(release_is_ready(decision))


if __name__ == "__main__":
    unittest.main()
