"""A small Redis REST rate limiter shared by every Cognix API instance.

Upstash is already the optional queue/cache provider.  Reusing it here avoids
per-process rate-limit windows when Render scales or restarts the API.
"""

from __future__ import annotations

import hashlib
import os

import httpx


def configured() -> bool:
    return bool(
        os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
        and os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    )


def allow(identity: str, *, limit: int, window_seconds: int = 60) -> bool | None:
    """Return a distributed allow decision, or ``None`` when Redis is unavailable.

    The identity is hashed before it becomes a Redis key so a bearer token or
    source IP is never stored verbatim in the shared service.
    """
    url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if not url or not token:
        return None

    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    key = f"cognix:rate-limit:{digest}"
    try:
        response = httpx.post(
            f"{url}/pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json=[["INCR", key], ["EXPIRE", key, str(window_seconds), "NX"]],
            timeout=3,
        )
        response.raise_for_status()
        results = response.json()
        count = int(results[0]["result"])
        return count <= limit
    except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError):
        return None
