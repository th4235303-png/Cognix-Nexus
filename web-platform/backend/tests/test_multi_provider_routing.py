import os
import unittest
from unittest.mock import patch

from app.services.embeddings import EmbeddingProvider, EmbeddingRoute
from app.services.llm import LLMProvider


class MultiProviderRoutingTests(unittest.TestCase):
    def test_all_llm_provider_keys_build_routes(self):
        env = {
            "GEMINI_API_KEY": "x",
            "OPENROUTER_API_KEY": "x",
            "MISTRAL_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "GROQ_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = LLMProvider()
            names = [route.name for route in provider.configured_routes]
            models = {route.name: route.model for route in provider.configured_routes}
        self.assertEqual(models["openrouter"], "openrouter/free")
        self.assertEqual(models["groq"], "qwen/qwen3.8-27b")
        self.assertEqual(models["mistral"], "ministral-8b-latest")
        self.assertEqual(models["cohere"], "command-r7b-12-2024")
        self.assertEqual(models["cloudflare"], "@cf/meta/llama-3.1-8b-instruct")
        self.assertEqual(
            names,
            ["gemini", "openrouter", "mistral", "cohere", "groq", "cloudflare"],
        )

    def test_weighted_schedule_defaults_to_equal_distribution(self):
        env = {
            "GEMINI_API_KEY": "x",
            "OPENROUTER_API_KEY": "x",
            "HUGGINGFACE_API_KEY": "x",
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



class CloudflareEmbeddingResponseTests(unittest.IsolatedAsyncioTestCase):
    async def test_cloudflare_openai_compatible_embedding_response(self):
        vector = [0.25] * 1024

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"data": [{"embedding": vector, "index": 0}]}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, traceback):
                return False

            async def post(self, *args, **kwargs):
                return FakeResponse()

        route = EmbeddingRoute(
            "cloudflare",
            "CLOUDFLARE_API_TOKEN",
            "https://example.invalid/ai/v1/embeddings",
            "@cf/baai/bge-large-en-v1.5",
            (1024,),
        )
        with patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": "test-token"}, clear=True):
            with patch("app.services.embeddings.httpx.AsyncClient", return_value=FakeClient()):
                provider = EmbeddingProvider()
                provider.dimension = 1024
                vectors = await provider.embed_on_route(route, ["probe"])
        self.assertEqual(len(vectors), 1)
        self.assertEqual(len(vectors[0]), 1024)
        self.assertEqual(vectors[0][0], 0.25)


if __name__ == "__main__":
    unittest.main()
