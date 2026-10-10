import os
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.services.level_up import feynman_grade, interleave, synthesis_contract, detect_sync_conflict, analyze_gap, build_learning_path, decision_balance, writing_citation_check
from app.services.llm import LLMProvider

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

    def test_learning_path_is_library_only(self):
        result = build_learning_path([
            {"source_type": "book", "title": "Book", "priority": 2},
            {"source_type": "web", "title": "External", "priority": 99},
        ], "learn")
        self.assertTrue(result["library_only"])
        self.assertEqual([x["title"] for x in result["items"]], ["Book"])

    def test_gap_is_explicit(self):
        result = analyze_gap("python", ["syntax"], ["syntax", "asyncio"])
        self.assertEqual(result["gaps"], ["asyncio"])
        self.assertEqual(result["status"], "open")

    def test_decision_support_does_not_select_an_option(self):
        result = decision_balance([{ "id": "a" }, { "id": "b" }], [{"option_id": "a", "source_id": "s1"}])
        self.assertEqual(result["options"], {"a": 1, "b": 0})
        self.assertTrue(result["needs_more_evidence"])
        self.assertNotIn("winner", result)

    def test_writing_citation_contract(self):
        self.assertTrue(writing_citation_check(["s1", "s2"], ["s1"])["valid"])
        self.assertEqual(writing_citation_check(["s1"], ["s2"])["missing_source_ids"], ["s2"])

    def test_llm_provider_uses_provider_key_not_render_model_overrides(self):
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "test-key",
                "COGNIX_AI_BASE_URL": "https://ai.invalid",
                "COGNIX_AI_MODEL": "test-model",
                "COGNIX_GROQ_MODEL": "override-model",
            },
            clear=True,
        ):
            provider = LLMProvider()
        self.assertTrue(provider.configured)
        self.assertEqual(provider.configured_routes[0].model, "qwen/qwen3.8-27b")

    def test_feature_matrix_contains_all_20(self):
        response = self.client.get("/brain/level-up/feature-matrix")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["features"]), 20)

if __name__ == "__main__":
    unittest.main()
