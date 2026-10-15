from __future__ import annotations

"""Render external health check.

Checks the Cognix API service deployed on Render by calling /health and /ready.
Reports status, response time, persistence_mode, and revision.

Never prints secret values. Only prints env var names (present/absent).
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# All env var keys declared in the render.yaml blueprint (both services, deduplicated).
# Extracted statically so the script has no runtime dependency on PyYAML.
RENDER_YAML_ENV_VAR_KEYS: list[str] = [
    "COGNIX_CORS_ORIGINS",
    "COGNIX_ALLOWED_HOSTS",
    "COGNIX_RATE_LIMIT_PER_MINUTE",
    "COGNIX_RATE_LIMIT_MAX_IDENTITIES",
    "COGNIX_REQUIRE_DATABASE",
    "DATABASE_URL",
    "COGNIX_AUTH_REQUIRED",
    "COGNIX_JWT_JWKS_URL",
    "COGNIX_JWT_ISSUER",
    "COGNIX_JWT_AUDIENCE",
    "COGNIX_PROCESSING_PROVIDER",
    "GEMINI_API_KEY",
    "OPENROUTER_API_KEY",
    "HUGGINGFACE_API_KEY",
    "MISTRAL_API_KEY",
    "COHERE_API_KEY",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID",
    "COGNIX_DRIVE_PROVIDER",
    "COGNIX_BOOK_STORAGE_PROVIDER",
    "COGNIX_B2_LARGE_FILE_THRESHOLD_BYTES",
    "COGNIX_MAX_BOOK_UPLOAD_BYTES",
    "COGNIX_MEDIA_STORAGE_PROVIDER",
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
    "CLOUDINARY_RESOURCE_TYPE",
    "CLOUDINARY_DELIVERY_TYPE",
    "CLOUDINARY_MAX_RAW_BYTES",
    "COGNIX_B2_ENDPOINT",
    "COGNIX_B2_BUCKET",
    "COGNIX_B2_KEY_ID",
    "COGNIX_B2_APPLICATION_KEY",
    "COGNIX_B2_REGION",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "COGNIX_SUPABASE_STORAGE_BUCKET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "GOOGLE_REFRESH_TOKEN",
    "GOOGLE_DRIVE_ROOT_FOLDER_ID",
    "SENTRY_DSN",
    # Worker-only keys
    "COGNIX_WORKER_POLL_SECONDS",
]


def fetch_endpoint(base_url: str, path: str, timeout: int) -> dict:
    """GET a single endpoint and return timing + parsed body."""
    url = base_url.rstrip("/") + path
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.monotonic() - start) * 1000
            raw = resp.read()
            status_code = resp.status
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw": raw.decode("utf-8", errors="replace")}
        return {
            "url_path": path,
            "http_status": status_code,
            "response_time_ms": round(elapsed_ms, 2),
            "ok": 200 <= status_code < 300,
            "body": body,
        }
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "url_path": path,
            "http_status": exc.code,
            "response_time_ms": round(elapsed_ms, 2),
            "ok": False,
            "error": str(exc),
        }
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "url_path": path,
            "http_status": None,
            "response_time_ms": round(elapsed_ms, 2),
            "ok": False,
            "error": type(exc).__name__ + ": " + str(exc),
        }


def compare_env_vars() -> dict:
    """Report which render.yaml env var names are present/absent — never prints values."""
    present = []
    absent = []
    for key in RENDER_YAML_ENV_VAR_KEYS:
        if os.getenv(key, "").strip():
            present.append(key)
        else:
            absent.append(key)
    return {
        "render_yaml_total": len(RENDER_YAML_ENV_VAR_KEYS),
        "present_count": len(present),
        "absent_count": len(absent),
        "present": sorted(present),
        "absent": sorted(absent),
        "secret_values_printed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render external health check")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--compare-env-vars",
        action="store_true",
        help=(
            "Read the list of expected env var names from the render.yaml blueprint "
            "and report which are configured (present/absent). Values are never printed."
        ),
    )
    args = parser.parse_args()

    base_url = os.getenv("COGNIX_API_BASE_URL", "").strip()
    if not base_url:
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "error": "COGNIX_API_BASE_URL environment variable is not set or empty",
                    "secret_values_printed": False,
                },
                indent=2,
            )
        )
        return 1

    health = fetch_endpoint(base_url, "/health", args.timeout)
    ready = fetch_endpoint(base_url, "/ready", args.timeout)

    # Extract well-known fields surfaced by Cognix health responses.
    health_body = health.get("body", {})
    persistence_mode = health_body.get("persistence_mode") or health_body.get("database")
    revision = health_body.get("revision") or health_body.get("git_revision") or health_body.get("version")

    overall_ok = health["ok"] and ready["ok"]
    result: dict = {
        "status": "PASS" if overall_ok else "FAIL",
        "secret_values_printed": False,
        "base_url_configured": True,  # present (value not printed)
        "response_time_ms": {
            "health": health["response_time_ms"],
            "ready": ready["response_time_ms"],
        },
        "persistence_mode": persistence_mode,
        "revision": revision,
        "endpoints": {
            "health": health,
            "ready": ready,
        },
    }

    if args.compare_env_vars:
        result["env_var_inventory"] = compare_env_vars()

    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
