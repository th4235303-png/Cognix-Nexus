from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class LLMRoute:
    name: str
    api_key_env: str
    url: str
    model: str


# Provider endpoints and model IDs are maintained here, not in Render settings.
# A provider is eligible only when its own API key is present.
_DEFAULT_ROUTES: tuple[LLMRoute, ...] = (
    LLMRoute("gemini", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-2.5-flash"),
    LLMRoute("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free"),
    # Keep Hugging Face enabled; availability depends on account inference credit
    # and the providers currently serving the selected model.
    LLMRoute("huggingface", "HUGGINGFACE_API_KEY", "https://router.huggingface.co/v1/chat/completions", "openai/gpt-oss-120b:cheapest"),
    LLMRoute("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/chat/completions", "ministral-8b-latest"),
    LLMRoute("cohere", "COHERE_API_KEY", "https://api.cohere.ai/compatibility/v1/chat/completions", "command-a-03-2025"),
    LLMRoute("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "qwen/qwen3.8-27b"),
    LLMRoute("cloudflare", "CLOUDFLARE_API_TOKEN", "", "@cf/meta/llama-3.1-8b-instruct"),
)


class LLMProvider:
    """Code-configured multi-provider LLM router with round-robin failover.

    Render stores provider credentials only. Endpoints and model IDs are
    version-controlled here so deployment configuration cannot silently drift.
    Secret values are never logged.
    """

    def __init__(self) -> None:
        self.timeout = 90.0
        self.last_provider_url: str | None = None
        self.last_provider: str | None = None
        self._cursor = 0

    @property
    def configured_routes(self) -> list[LLMRoute]:
        routes: list[LLMRoute] = []
        for route in _DEFAULT_ROUTES:
            if not os.getenv(route.api_key_env, "").strip():
                continue
            url = route.url
            if route.name == "cloudflare":
                account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
                if not account_id:
                    continue
                url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
            routes.append(LLMRoute(route.name, route.api_key_env, url, route.model))
        return routes

    @property
    def configured(self) -> bool:
        return bool(self.configured_routes)

    @property
    def provider_urls(self) -> list[str]:
        return [route.url for route in self.configured_routes]

    def _schedule(self) -> list[LLMRoute]:
        routes = self.configured_routes
        if not routes:
            return []
        start = self._cursor % len(routes)
        self._cursor += 1
        return routes[start:] + routes[:start]

    async def complete_on_route(self, route: LLMRoute, system: str, user: str) -> str:
        """Call one concrete provider route without failover, for release E2E."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv(route.api_key_env, '').strip()}",
        }
        payload = {
            "model": route.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if route.name != "gemini":
            payload["temperature"] = 0.1
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(route.url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM provider returned an unexpected response") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LLM provider returned empty content")
        self.last_provider = route.name
        self.last_provider_url = route.url
        return content.strip()

    async def complete(self, system: str, user: str) -> str:
        routes = self._schedule()
        if not routes:
            raise RuntimeError("No LLM provider is configured; add at least one provider API key")

        errors: list[str] = []
        for route in routes:
            try:
                return await self.complete_on_route(route, system, user)
            except Exception as exc:
                # Never include credentials or raw provider response bodies.
                errors.append(f"{route.name}: {type(exc).__name__}")
        raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))


llm_provider = LLMProvider()
