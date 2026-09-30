from __future__ import annotations

import hashlib
import hmac
import json
import os

import httpx


def configured() -> bool:
    return bool(os.getenv("LOGIXA_FLOW_WEBHOOK_URL", "").strip())


def deliver(event: dict) -> dict:
    url = os.getenv("LOGIXA_FLOW_WEBHOOK_URL", "").strip()
    if not url:
        raise RuntimeError("Logixa Flow webhook is not configured")
    secret = os.getenv("LOGIXA_FLOW_WEBHOOK_SECRET", "").strip()
    body = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest() if secret else ""
    headers = {"Content-Type": "application/json", "X-Cognix-Event": "approved_knowledge"}
    if signature:
        headers["X-Cognix-Signature"] = signature
    response = httpx.post(url, content=body, headers=headers, timeout=20.0)
    response.raise_for_status()
    return {"status": "delivered", "http_status": response.status_code}
