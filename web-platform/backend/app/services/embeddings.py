from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

import httpx


@dataclass(frozen=True)
class EmbeddingRoute:
    name: str
    api_key_env: str
    url: str
    model: str
    dimensions: tuple[int, ...]


_DEFAULT_ROUTES: tuple[EmbeddingRoute, ...] = (
    EmbeddingRoute(
        "openrouter",
        "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1/embeddings",
        "openai/text-embedding-3-small",
        (1536,),
    ),
    EmbeddingRoute(
        "cohere",
        "COHERE_API_KEY",
        "https://api.cohere.com/v2/embed",
        "embed-v5.0-pro",
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


def _weights() -> dict[str, int]:
    weights: dict[str, int] = {}
    raw = os.getenv("COGNIX_EMBEDDING_PROVIDER_WEIGHTS", "")
    for item in raw.split(","):
        if "=" not in item:
            continue
        name, value = item.split("=", 1)
        try:
            parsed = int(value.strip())
        except ValueError:
            continue
        if parsed > 0:
            weights[name.strip().lower()] = parsed
    return weights


class EmbeddingProvider:
    """Weighted embedding router constrained by the persisted vector dimension.

    The current Cognix schema uses vector(1536), so only routes that can emit
    1536-dimensional vectors are eligible by default. Voyage and Cloudflare
    become eligible automatically if the configured dimension is changed to a
    dimension those providers support.
    """

    def __init__(self) -> None:
        self.dimension = int(os.getenv("COGNIX_EMBEDDING_DIMENSION", "1536"))
        self.url = os.getenv("COGNIX_EMBEDDING_API_URL", "").strip()
        self.api_key = os.getenv("COGNIX_EMBEDDING_API_KEY", "").strip()
        self.model = os.getenv("COGNIX_EMBEDDING_MODEL", "").strip()
        self.last_provider: str | None = None
        self._cursor = 0

    @property
    def configured_routes(self) -> list[EmbeddingRoute]:
        weights = _weights()
        routes: list[EmbeddingRoute] = []
        for route in _DEFAULT_ROUTES:
            if self.dimension not in route.dimensions:
                continue
            key = os.getenv(route.api_key_env, "").strip()
            if not key:
                continue
            url = (os.getenv(f"COGNIX_{route.name.upper()}_EMBEDDING_API_URL") or route.url).strip()
            model = (os.getenv(f"COGNIX_{route.name.upper()}_EMBEDDING_MODEL") or route.model).strip()
            if route.name == "cloudflare":
                account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
                if not account_id:
                    continue
                url = url or f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/embeddings"
            routes.append(route.__class__(route.name, route.api_key_env, url, model, route.dimensions))
        return routes

    @property
    def configured(self) -> bool:
        return bool(self.configured_routes) or bool(self.url and self.model)

    def _schedule(self) -> list[EmbeddingRoute]:
        routes = self.configured_routes
        if not routes:
            return []
        # Equal distribution by default; optional provider weights allow deliberate
        # cost/latency tuning without changing code.
        weighted = []
        weights = _weights()
        for route in routes:
            weighted.extend([route] * max(1, weights.get(route.name, 1)))
        start = self._cursor % len(weighted)
        self._cursor += 1
        return weighted[start:] + weighted[:start]

    async def _request(self, route: EmbeddingRoute, inputs: Sequence[str]) -> list[list[float]]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv(route.api_key_env, '').strip()}",
        }
        payload = {"model": route.model, "input": list(inputs)}
        if route.name == "openrouter":
            payload["dimensions"] = self.dimension
        elif route.name == "cohere":
            payload = {
                "model": route.model,
                "texts": list(inputs),
                "input_type": "search_document",
                "output_dimension": self.dimension,
                "embedding_types": ["float"],
            }
        elif route.name == "voyage":
            payload["output_dimension"] = self.dimension
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(route.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()

        if route.name == "cohere":
            vectors = body.get("embeddings", {}).get("float", [])
        elif route.name == "cloudflare":
            data = body.get("data", [])
            vectors = data if data and isinstance(data[0], list) else body.get("result", {}).get("data", [])
            if vectors and isinstance(vectors[0], dict):
                vectors = [item.get("embedding", []) for item in vectors]
        else:
            vectors = [
                item["embedding"]
                for item in sorted(body.get("data", []), key=lambda item: item.get("index", 0))
            ]
        if len(vectors) != len(inputs):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        if any(len(vector) != self.dimension for vector in vectors):
            raise RuntimeError(f"Embedding dimension mismatch; expected {self.dimension}")
        self.last_provider = route.name
        return vectors

    async def embed_on_route(self, route: EmbeddingRoute, inputs: Sequence[str]) -> list[list[float]]:
        """Call one concrete embedding route without failover."""
        return await self._request(route, inputs)

    async def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        if not self.configured:
            raise RuntimeError("Semantic embeddings are not configured")

        errors: list[str] = []
        routes = self._schedule()
        if routes:
            for route in routes:
                try:
                    return await self.embed_on_route(route, inputs)
                except Exception as exc:
                    errors.append(f"{route.name}: {type(exc).__name__}")
            raise RuntimeError("All configured embedding providers failed: " + "; ".join(errors))

        # Legacy single-provider configuration remains supported.
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "input": list(inputs), "dimensions": self.dimension}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        vectors = [
            item["embedding"]
            for item in sorted(body.get("data", []), key=lambda item: item.get("index", 0))
        ]
        if len(vectors) != len(inputs) or any(len(vector) != self.dimension for vector in vectors):
            raise RuntimeError(f"Embedding dimension mismatch; expected {self.dimension}")
        self.last_provider = "legacy"
        return vectors


embedding_provider = EmbeddingProvider()
