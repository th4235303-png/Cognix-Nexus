import os

import httpx
import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient


PUBLIC_PATHS = {"/", "/health", "/ready", "/docs", "/openapi.json", "/redoc", "/integrations/google-drive/callback"}


def auth_required() -> bool:
    return os.getenv("COGNIX_AUTH_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}


def _decode_token(token: str) -> dict:
    secret = os.getenv("COGNIX_JWT_SECRET", "").strip()
    jwks_url = os.getenv("COGNIX_JWT_JWKS_URL", "").strip()
    issuer = os.getenv("COGNIX_JWT_ISSUER", "").strip()
    audience = os.getenv("COGNIX_JWT_AUDIENCE", "").strip()
    options = {"verify_signature": True, "verify_exp": True, "verify_aud": bool(audience)}
    kwargs: dict[str, object] = {}
    if issuer:
        kwargs["issuer"] = issuer
    if audience:
        kwargs["audience"] = audience

    try:
        if secret:
            return jwt.decode(token, secret, algorithms=["HS256"], options=options, **kwargs)
        if jwks_url:
            key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
            return jwt.decode(token, key, algorithms=["RS256", "ES256"], options=options, **kwargs)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Invalid or expired bearer token"}) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "AUTH_PROVIDER_UNAVAILABLE", "message": "Authentication provider is unavailable"}) from exc

    raise RuntimeError("JWT verification is not configured")


def _verify_with_supabase(token: str) -> dict:
    base_url = os.getenv("COGNIX_SUPABASE_URL", "").strip().rstrip("/")
    publishable_key = os.getenv("COGNIX_SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not base_url or not publishable_key:
        raise HTTPException(
            status_code=503,
            detail={"code": "AUTH_NOT_CONFIGURED", "message": "Authentication is enabled but JWT verification is not configured"},
        )

    try:
        response = httpx.get(
            f"{base_url}/auth/v1/user",
            headers={"apikey": publishable_key, "Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Invalid or expired bearer token"})
        response.raise_for_status()
        user = response.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "AUTH_PROVIDER_UNAVAILABLE", "message": "Authentication provider is unavailable"}) from exc

    subject = user.get("id")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Token subject is required"})
    return {"sub": subject, "role": "authenticated", "email": user.get("email")}


def authenticate_request(request: Request) -> dict:
    if not auth_required() or request.url.path in PUBLIC_PATHS:
        return {"sub": "anonymous"}

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Bearer token required"})

    token = header[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Bearer token required"})

    if os.getenv("COGNIX_JWT_SECRET", "").strip() or os.getenv("COGNIX_JWT_JWKS_URL", "").strip():
        return _decode_token(token)

    return _verify_with_supabase(token)
