from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

import httpx


@dataclass(frozen=True)
class LLMRoute:
    name: str
    api_key_env: str
    url: str
    model: str
    weight: int = 1


_DEFAULT_ROUTES: tuple[LLMRoute, ...] = (
    LLMRoute("gemini", "GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.8-flash"),
    LLMRoute("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free"),
    # Hugging Face documents this model and the cheapest-provider routing suffix.
    # HF Free accounts still have a small monthly credit allowance; model choice
    # cannot make an exhausted account's HTTP 402 free again.
    LLMRoute("huggingface", "HUGGINGFACE_API_KEY", "https://router.huggingface.co/v1/chat/completions", "openai/gpt-oss-120b:cheapest"),
    # Mistral Studio Free mode is limited; use the documented small API model.
    LLMRoute("mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1/chat/completions", "mistral-small-latest"),
    LLMRoute("cohere", "COHERE_API_KEY", "https://api.cohere.ai/compatibility/v1/chat/completions", "command-a-plus-05-2026"),
    LLMRoute("groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b"),
    # GLM-5.2 requires a paid Workers plan/AI Gateway credits. Use a model eligible
    # for Workers AI's 10,000-neuron daily free allocation instead.
    LLMRoute("cloudflare", "CLOUDFLARE_API_TOKEN", "", "@cf/meta/llama-3.1-8b-instruct-fp8-fast"),
)


def _env_override(name: str, suffix: str, default: str) -> str:
    return (os.getenv(f"COGNIX_{name.upper()}_{suffix}") or default).strip()


def _weights() -> dict[str, int]:
    weights: dict[str, int] = {}
    raw = os.getenv("COGNIX_LLM_PROVIDER_WEIGHTS", "")
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


class LLMProvider:
    """Multi-provider OpenAI-compatible router with weighted distribution and failover.

    Provider-specific keys stay in environment variables. No secret value is logged.
    If provider keys are absent, the legacy COGNIX_LLM_* / COGNIX_AI_* configuration
    remains supported for backwards compatibility.
    """

    def __init__(self) -> None:
        self.timeout = float(os.getenv("COGNIX_LLM_TIMEOUT_SECONDS", "90"))
        self.last_provider_url: str | None = None
        self.last_provider: str | None = None
        self._cursor = 0

        self.url = (os.getenv("COGNIX_LLM_API_URL") or os.getenv("COGNIX_AI_BASE_URL") or "").strip()
        self.api_key = (
            os.getenv("COGNIX_LLM_API_KEY")
            or os.getenv("COGNIX_AI_API_KEY")
            or os.getenv("COGNIX_EMBEDDING_API_KEY")
            or ""
        ).strip()
        self.model = (os.getenv("COGNIX_LLM_MODEL") or os.getenv("COGNIX_AI_MODEL") or "").strip()
        raw_fallbacks = os.getenv("COGNIX_LLM_FALLBACK_URLS", "")
        self.fallback_urls = [item.strip() for item in raw_fallbacks.split(",") if item.strip()]

    @property
    def configured_routes(self) -> list[LLMRoute]:
        weights = _weights()
        routes: list[LLMRoute] = []
        for route in _DEFAULT_ROUTES:
            key = os.getenv(route.api_key_env, "").strip()
            if not key:
                continue
            url = _env_override(route.name, "API_URL", route.url)
            model = _env_override(route.name, "MODEL", route.model)
            # Cloudflare's OpenAI-compatible endpoint requires the account id.
            if route.name == "cloudflare":
                account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
                if not account_id:
                    continue
                url = url or f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
            weight = weights.get(route.name, route.weight)
            routes.append(LLMRoute(route.name, route.api_key_env, url, model, weight))
        return routes

    @property
    def configured(self) -> bool:
        return bool(self.configured_routes) or bool(self.url and self.model)

    @property
    def provider_urls(self) -> list[str]:
        routes = self.configured_routes
        if routes:
            return [route.url for route in routes]
        return list(dict.fromkeys([self.url, *self.fallback_urls])) if self.url else []

    def _schedule(self) -> list[LLMRoute]:
        routes = self.configured_routes
        if not routes:
            return []
        expanded = [route for route in routes for _ in range(max(1, route.weight))]
        if not expanded:
            return []
        start = self._cursor % len(expanded)
        self._cursor += 1
        return expanded[start:] + expanded[:start]

    async def complete_on_route(self, route: LLMRoute, system: str, user: str) -> str:
        """Call one concrete configured route without failover.

        Release E2E uses this to prove each configured provider independently.
        Secret values are never included in errors or logs.
        """
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
        if not self.configured:
            raise RuntimeError("LLM synthesis is not configured")

        errors: list[str] = []
        routes = self._schedule()
        if routes:
            for route in routes:
                try:
                    return await self.complete_on_route(route, system, user)
                except Exception as exc:
                    errors.append(f"{route.name}: {type(exc).__name__}")
            raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))

        # Legacy single-provider mode.
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
                content = body["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise RuntimeError("LLM provider returned empty content")
                self.last_provider = "legacy"
                self.last_provider_url = url
                return content.strip()
            except Exception as exc:
                errors.append(f"legacy: {type(exc).__name__}")
        raise RuntimeError("All configured LLM providers failed: " + "; ".join(errors))


llm_provider = LLMProvider()
