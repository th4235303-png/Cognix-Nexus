import unittest

from app.services.learning_science.contracts import LearningSignal, decay_weight


class Phase14LearningContractTests(unittest.TestCase):
    def test_decay_is_deterministic(self):
        self.assertEqual(decay_weight(0, 30), 1.0)
        self.assertEqual(decay_weight(30, 30), 0.5)

    def test_learning_signal_requires_evidence_shape(self):
        signal = LearningSignal(
            id="signal-1",
            subject_id="subject-1",
            signal_type="recall",
            strength=0.8,
            occurred_at="2026-10-08T00:00:00+00:00",
            evidence_refs=(),
        )
        self.assertEqual(signal.subject_id, "subject-1")
        self.assertEqual(signal.evidence_refs, ())


if __name__ == "__main__":
    unittest.main()
