from __future__ import annotations
import os
from urllib.parse import quote
import httpx


def redis_ping() -> bool:
    url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if not url or not token:
        return False
    try:
        r = httpx.get(f"{url}/ping", headers={"Authorization": f"Bearer {token}"}, timeout=3)
        return r.is_success and str(r.json().get("result", "")).upper() == "PONG"
    except Exception:
        return False


def redis_set(key: str, value: str, ttl: int = 3600) -> bool:
    url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if not url or not token:
        return False
    try:
        r = httpx.get(f"{url}/set/{quote(key, safe='')}/{quote(value, safe='')}/EX/{ttl}", headers={"Authorization": f"Bearer {token}"}, timeout=3)
        return r.is_success
    except Exception:
        return False


def publish_qstash(payload: dict) -> dict:
    base = os.getenv("QSTASH_URL", "https://qstash.upstash.io").rstrip("/")
    token = os.getenv("QSTASH_TOKEN", "").strip()
    callback = os.getenv("QSTASH_CALLBACK_URL", "").strip()
    callback_token = os.getenv("QSTASH_CALLBACK_TOKEN", "").strip()
    if not token or not callback:
        return {"published": False, "reason": "qstash_not_configured"}
    try:
        r = httpx.post(
            f"{base}/v2/publish/{quote(callback, safe='')}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Upstash-Forward-Authorization": f"Bearer {callback_token}",
            },
            json=payload,
            timeout=5,
        )
        r.raise_for_status()
        return {"published": True, **r.json()}
    except Exception as exc:
        return {"published": False, "reason": type(exc).__name__}


def enqueue_processing(task_id: str, source_id: str) -> dict:
    redis_set(f"cognix:processing:wakeup:{task_id}", source_id)
    return publish_qstash({"task_id": task_id, "source_id": source_id})
