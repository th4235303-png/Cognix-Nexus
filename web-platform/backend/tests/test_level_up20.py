import unittest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.services.level_up import feynman_grade, interleave, synthesis_contract, detect_sync_conflict

class LevelUpTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_feynman_mastery_threshold(self):
        result = feynman_grade("A system stores facts in a structured database.", ["system", "database"])
        self.assertTrue(result["mastered"])

    def test_interleaving_requires_two_subjects(self):
        self.assertEqual(interleave(["math", "history"], 2), ["math", "history", "math", "history"])
        with self.assertRaises(ValueError):
            interleave(["math"], 2)

    def test_synthesis_requires_three_sources(self):
        with self.assertRaises(ValueError):
            synthesis_contract("q", ["a", "b"], [])
        result = synthesis_contract("q", ["a", "b", "c"], [{"source_id":"a","text":"evidence"}])
        self.assertEqual(result["source_count"], 3)

    def test_sync_conflict_is_explicit(self):
        result = detect_sync_conflict(2, 3, 4, {"x":1}, {"x":2})
        self.assertTrue(result["conflict"])

    def test_policy_boundaries(self):
        self.assertEqual(self.client.get("/brain/level-up/mood-policy").json()["storage"], "local_only")
        self.assertFalse(self.client.get("/brain/level-up/ambient-policy").json()["background_listening"])
        self.assertTrue(self.client.get("/brain/level-up/legacy/policy").json()["encrypted"])

if __name__ == "__main__":
    unittest.main()
