import os
import unittest
from unittest.mock import patch

from app.services.embeddings import EmbeddingProvider, EmbeddingRoute
from app.services.llm import LLMProvider


class MultiProviderRoutingTests(unittest.TestCase):
    def test_provider_keys_build_code_defined_routes(self):
        env = {
            "GEMINI_API_KEY": "x",
            "OPENROUTER_API_KEY": "x",
            "HUGGINGFACE_API_KEY": "x",
            "MISTRAL_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "GROQ_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "COGNIX_GROQ_MODEL": "this-override-must-be-ignored",
            "COGNIX_GROQ_API_URL": "https://override.invalid",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = LLMProvider()
            routes = provider.configured_routes
            names = [route.name for route in routes]
            groq = next(route for route in routes if route.name == "groq")
            cloudflare = next(route for route in routes if route.name == "cloudflare")
        self.assertEqual(
            names,
            ["gemini", "openrouter", "huggingface", "mistral", "cohere", "groq", "cloudflare"],
        )
        self.assertEqual(groq.model, "qwen/qwen3.8-27b")
        self.assertEqual(groq.url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(
            cloudflare.url,
            "https://api.cloudflare.com/client/v4/accounts/account/ai/v1/chat/completions",
        )

    def test_round_robin_schedule_rotates_provider_priority(self):
        env = {
            "OPENROUTER_API_KEY": "x",
            "HUGGINGFACE_API_KEY": "x",
            "MISTRAL_API_KEY": "x",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = LLMProvider()
            first = [route.name for route in provider._schedule()]
            second = [route.name for route in provider._schedule()]
        self.assertEqual(second, first[1:] + first[:1])

    def test_embedding_uses_only_dimension_compatible_provider(self):
        env = {
            "OPENROUTER_API_KEY": "x",
            "COHERE_API_KEY": "x",
            "VOYAGE_API_KEY": "x",
            "CLOUDFLARE_API_TOKEN": "x",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "COGNIX_EMBEDDING_DIMENSION": "1024",
            "COGNIX_EMBEDDING_MODEL": "this-override-must-be-ignored",
        }
        with patch.dict(os.environ, env, clear=True):
            provider = EmbeddingProvider()
            self.assertEqual(provider.dimension, 1536)
            self.assertEqual([route.name for route in provider.configured_routes], ["cohere"])
            self.assertEqual(provider.configured_routes[0].model, "embed-v4.0")


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
