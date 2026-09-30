import os

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient


PUBLIC_PATHS = {"/", "/health", "/ready", "/docs", "/openapi.json", "/redoc"}


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
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options=options,
                **kwargs,
            )
        if not jwks_url:
            raise RuntimeError("JWT verification is not configured")
        key = PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
        return jwt.decode(
            token,
            key,
            algorithms=["RS256", "ES256"],
            options=options,
            **kwargs,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Invalid or expired bearer token"}) from exc


def authenticate_request(request: Request) -> dict:
    if not auth_required() or request.url.path in PUBLIC_PATHS:
        return {"sub": "anonymous"}

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Bearer token required"})

    token = header[7:].strip()
    if not os.getenv("COGNIX_JWT_SECRET", "").strip() and not os.getenv("COGNIX_JWT_JWKS_URL", "").strip():
        raise HTTPException(status_code=503, detail={"code": "AUTH_NOT_CONFIGURED", "message": "Authentication is enabled but JWT verification is not configured"})

    claims = _decode_token(token)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Token subject is required"})
    return claims
