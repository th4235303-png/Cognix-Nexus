from __future__ import annotations

import os
from typing import Sequence

import httpx


class LLMProvider:
    """Vendor-neutral OpenAI-compatible provider router with ordered fallback."""

    def __init__(self) -> None:
        self.url = (os.getenv("COGNIX_LLM_API_URL") or os.getenv("COGNIX_AI_BASE_URL") or "").strip()
        self.api_key = (os.getenv("COGNIX_LLM_API_KEY") or os.getenv("COGNIX_AI_API_KEY") or "").strip()
        self.model = (os.getenv("COGNIX_LLM_MODEL") or os.getenv("COGNIX_AI_MODEL") or "").strip()
        raw_fallbacks = os.getenv("COGNIX_LLM_FALLBACK_URLS", "")
        self.fallback_urls = [item.strip() for item in raw_fallbacks.split(",") if item.strip()]
        self.timeout = float(os.getenv("COGNIX_LLM_TIMEOUT_SECONDS", "90"))
        self.last_provider_url: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.url and self.model)

    @property
    def provider_urls(self) -> list[str]:
        return list(dict.fromkeys([self.url, *self.fallback_urls])) if self.url else []

    async def complete(self, system: str, user: str) -> str:
        if not self.configured:
            raise RuntimeError("LLM synthesis is not configured")
        errors: list[str] = []
        for url in self.provider_urls:
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
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    body = response.json()
                try:
                    content = body["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise RuntimeError("LLM provider returned an unexpected response") from exc
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("LLM provider returned empty content")
                self.last_provider_url = url
                return content.strip()
            except Exception as exc:
                # Never expose provider response bodies or credentials in the API.
                errors.append(f"{url[:120]}: {type(exc).__name__}")
        raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))


llm_provider = LLMProvider()
