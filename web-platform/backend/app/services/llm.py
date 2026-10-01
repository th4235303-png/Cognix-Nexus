from __future__ import annotations

import os
from typing import Sequence

import httpx


class LLMProvider:
    """OpenAI-compatible chat adapter; vendor-neutral by configuration."""

    def __init__(self) -> None:
        self.url = (os.getenv("COGNIX_LLM_API_URL") or os.getenv("COGNIX_AI_BASE_URL") or "").strip()
        self.api_key = (os.getenv("COGNIX_LLM_API_KEY") or os.getenv("COGNIX_AI_API_KEY") or "").strip()
        self.model = (os.getenv("COGNIX_LLM_MODEL") or os.getenv("COGNIX_AI_MODEL") or "").strip()
        self.timeout = float(os.getenv("COGNIX_LLM_TIMEOUT_SECONDS", "90"))

    @property
    def configured(self) -> bool:
        return bool(self.url and self.model)

    async def complete(self, system: str, user: str) -> str:
        if not self.configured:
            raise RuntimeError("LLM synthesis is not configured")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM provider returned an unexpected response") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LLM provider returned empty content")
        return content.strip()


llm_provider = LLMProvider()
