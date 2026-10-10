from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

import httpx


# The persisted PostgreSQL schema uses vector(1536). Keep this dimension aligned
# with the database schema; changing it requires a migration and re-embedding.
VECTOR_DIMENSION = 1536


@dataclass(frozen=True)
class EmbeddingRoute:
    name: str
    api_key_env: str
    url: str
    model: str
    dimensions: tuple[int, ...]


# Endpoints and model IDs live in code. A route is enabled only if its provider
# key is present and it supports the database's fixed vector dimension.
_DEFAULT_ROUTES: tuple[EmbeddingRoute, ...] = (
    EmbeddingRoute(
        "openrouter",
        "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1/embeddings",
        "liquid/lfm-2.5-embedding-350m:free",
        (1024,),
    ),
    EmbeddingRoute(
        "cohere",
        "COHERE_API_KEY",
        "https://api.cohere.com/v2/embed",
        "embed-v4.0",
        (256, 512, 768, 1024, 1536, 2048),
    ),
    EmbeddingRoute(
        "voyage",
        "VOYAGE_API_KEY",
        "https://api.voyageai.com/v1/embeddings",
        "voyage-4",
        (256, 512, 1024, 2048),
    ),
    EmbeddingRoute(
        "cloudflare",
        "CLOUDFLARE_API_TOKEN",
        "",
        "@cf/baai/bge-large-en-v1.5",
        (1024,),
    ),
)


class EmbeddingProvider:
    """Code-configured embedding router compatible with persisted vector(1536)."""

    def __init__(self) -> None:
        self.dimension = VECTOR_DIMENSION
        self.last_provider: str | None = None
        self._cursor = 0

    @property
    def configured_routes(self) -> list[EmbeddingRoute]:
        routes: list[EmbeddingRoute] = []
        for route in _DEFAULT_ROUTES:
            if self.dimension not in route.dimensions:
                continue
            if not os.getenv(route.api_key_env, "").strip():
                continue
            url = route.url
            if route.name == "cloudflare":
                account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
                if not account_id:
                    continue
                url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/embeddings"
            routes.append(EmbeddingRoute(route.name, route.api_key_env, url, route.model, route.dimensions))
        return routes

    @property
    def configured(self) -> bool:
        return bool(self.configured_routes)

    @property
    def model(self) -> str:
        routes = self.configured_routes
        if self.last_provider:
            for route in routes:
                if route.name == self.last_provider:
                    return route.model
        return routes[0].model if routes else ""

    def _schedule(self) -> list[EmbeddingRoute]:
        routes = self.configured_routes
        if not routes:
            return []
        start = self._cursor % len(routes)
        self._cursor += 1
        return routes[start:] + routes[:start]

    async def _request(self, route: EmbeddingRoute, inputs: Sequence[str]) -> list[list[float]]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv(route.api_key_env, '').strip()}",
        }
        payload = {"model": route.model, "input": list(inputs)}
        if route.name == "cohere":
            payload = {
                "model": route.model,
                "texts": list(inputs),
                "input_type": "search_document",
                "output_dimension": self.dimension,
                "embedding_types": ["float"],
            }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(route.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        if route.name == "cohere":
            vectors = body.get("embeddings", {}).get("float", [])
        elif route.name == "cloudflare":
            data = body.get("data", [])
            if data and isinstance(data[0], dict):
                vectors = [
                    item.get("embedding", [])
                    for item in sorted(data, key=lambda item: item.get("index", 0))
                ]
            elif data and isinstance(data[0], list):
                vectors = data
            else:
                result_data = body.get("result", {}).get("data", [])
                if result_data and isinstance(result_data[0], dict):
                    vectors = [
                        item.get("embedding", [])
                        for item in sorted(result_data, key=lambda item: item.get("index", 0))
                    ]
                else:
                    vectors = result_data
        else:
            vectors = [
                item["embedding"]
                for item in sorted(body.get("data", []), key=lambda item: item.get("index", 0))
            ]
        if len(vectors) != len(inputs):
            raise RuntimeError(f"Embedding provider returned {len(vectors)} vectors; expected {len(inputs)}")
        if any(len(vector) != self.dimension for vector in vectors):
            raise RuntimeError(
                f"Embedding dimension mismatch; expected {self.dimension}, got {[len(vector) for vector in vectors]}"
            )
        self.last_provider = route.name
        return vectors

    async def embed_on_route(self, route: EmbeddingRoute, inputs: Sequence[str]) -> list[list[float]]:
        """Call one concrete embedding route without failover."""
        return await self._request(route, inputs)

    async def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        routes = self._schedule()
        if not routes:
            raise RuntimeError(
                "No embedding provider supports the database's 1536 dimensions; configure COHERE_API_KEY"
            )

        errors: list[str] = []
        for route in routes:
            try:
                return await self.embed_on_route(route, inputs)
            except Exception as exc:
                errors.append(f"{route.name}: {type(exc).__name__}")
        raise RuntimeError("All configured embedding providers failed: " + "; ".join(errors))


embedding_provider = EmbeddingProvider()
