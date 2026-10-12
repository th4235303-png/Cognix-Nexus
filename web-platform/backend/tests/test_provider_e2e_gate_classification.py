import unittest

from scripts.provider_e2e import _has_healthy_llm_route


class ProviderE2EGateClassificationTests(unittest.TestCase):
    def test_one_healthy_route_is_enough_when_optional_routes_fail(self):
        results = {
            "gemini": {"ok": False, "error": "HTTP_403"},
            "cohere": {"ok": True},
            "mistral": {"ok": False, "error": "HTTP_429"},
        }
        self.assertTrue(_has_healthy_llm_route(results))

    def test_all_failed_or_unconfigured_routes_block_llm_gate(self):
        results = {
            "gemini": {"ok": False, "error": "HTTP_403"},
            "cohere": {"ok": False, "error": "HTTP_401"},
            "mistral": {"ok": False, "error": "not_configured"},
        }
        self.assertFalse(_has_healthy_llm_route(results))

    def test_empty_route_matrix_blocks_llm_gate(self):
        self.assertFalse(_has_healthy_llm_route({}))


if __name__ == "__main__":
    unittest.main()
