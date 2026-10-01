from __future__ import annotations

import os
from typing import Sequence

import httpx


class EmbeddingProvider:
    """OpenAI-compatible embeddings adapter without hard-coding a vendor."""

    def __init__(self) -> None:
        self.url = os.getenv("COGNIX_EMBEDDING_API_URL", "").strip()
        self.api_key = os.getenv("COGNIX_EMBEDDING_API_KEY", "").strip()
        self.model = os.getenv("COGNIX_EMBEDDING_MODEL", "").strip()
        self.dimension = int(os.getenv("COGNIX_EMBEDDING_DIMENSION", "1536"))

    @property
    def configured(self) -> bool:
        return bool(self.url and self.model)

    async def embed(self, inputs: Sequence[str]) -> list[list[float]]:
        if not self.configured:
            raise RuntimeError("Semantic embeddings are not configured")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "input": list(inputs)}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        vectors = [item["embedding"] for item in sorted(body.get("data", []), key=lambda item: item.get("index", 0))]
        if len(vectors) != len(inputs):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        if any(len(vector) != self.dimension for vector in vectors):
            raise RuntimeError(f"Embedding dimension mismatch; expected {self.dimension}")
        return vectors


embedding_provider = EmbeddingProvider()
