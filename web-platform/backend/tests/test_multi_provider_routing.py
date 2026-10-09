import os
import unittest
from unittest.mock import patch

from app.services.embeddings import EmbeddingProvider
from app.services.llm import LLMProvider


class MultiProviderRoutingTests(unittest.TestCase):
    def test_all_llm_provider_keys_build_routes(self):
        env = {
            "GEMINI_API_KEY": "x",
            "OPENROUTER_API_KEY": "x",
            "HUGGINGFACE_API_KEY": "x",
            "CEREBRAS_API_KEY": "x",
            "MISTRAL_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "GROQ_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = LLMProvider()
            names = [route.name for route in provider.configured_routes]
            openrouter_model = next(route.model for route in provider.configured_routes if route.name == "openrouter")
        self.assertEqual(openrouter_model, "openrouter/free")
        self.assertEqual(
            names,
            ["gemini", "openrouter", "huggingface", "cerebras", "mistral", "cohere", "groq", "cloudflare"],
        )

    def test_weighted_schedule_defaults_to_equal_distribution(self):
        env = {
            "GEMINI_API_KEY": "x",
            "OPENROUTER_API_KEY": "x",
            "HUGGINGFACE_API_KEY": "x",
            "CEREBRAS_API_KEY": "x",
            "MISTRAL_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "GROQ_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = LLMProvider()
            first = [route.name for route in provider._schedule()]
            second = [route.name for route in provider._schedule()]
        self.assertEqual(second, first[1:] + first[:1])

    def test_embedding_dimension_selects_compatible_providers(self):
        env = {
            "OPENROUTER_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "VOYAGE_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "COGNIX_EMBEDDING_DIMENSION": "1536",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = EmbeddingProvider()
            self.assertEqual([r.name for r in provider.configured_routes], ["cohere"])

    def test_embedding_dimension_can_enable_voyage_and_cloudflare(self):
        env = {
            "COHERE_API_KEY": "x",
            "VOYAGE_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "OPENROUTER_API_KEY": "x",
            "COGNIX_EMBEDDING_DIMENSION": "1024",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = EmbeddingProvider()
            self.assertEqual([r.name for r in provider.configured_routes], ["openrouter", "cohere", "voyage", "cloudflare"])
            openrouter = next(r for r in provider.configured_routes if r.name == "openrouter")
            self.assertEqual(openrouter.model, "liquid/lfm-2.5-embedding-350m:free")


if __name__ == "__main__":
    unittest.main()
