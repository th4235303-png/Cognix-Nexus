import unittest

from app.services.learning_science.contracts import decay_weight
from app.services.life_integration.contracts import ContextRestoreRequest, can_restore

class FutureFoundationContractTests(unittest.TestCase):
    def test_learning_decay_is_deterministic(self):
        self.assertEqual(decay_weight(0, 10), 1.0)
        self.assertEqual(decay_weight(10, 10), 0.5)
        with self.assertRaises(ValueError):
            decay_weight(-1, 10)

    def test_context_restore_fails_closed(self):
        request = ContextRestoreRequest("r", "owner", False, ("book",), "resume")
        self.assertFalse(can_restore(request))
        request = ContextRestoreRequest("r", "owner", True, ("book",), "resume")
        self.assertTrue(can_restore(request))

if __name__ == "__main__":
    unittest.main()
