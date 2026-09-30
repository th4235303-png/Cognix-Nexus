import os

import jwt
from fastapi import HTTPException, Request


PUBLIC_PATHS = {"/", "/health", "/ready", "/docs", "/openapi.json", "/redoc"}


def auth_required() -> bool:
    return os.getenv("COGNIX_AUTH_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}


def authenticate_request(request: Request) -> dict:
    if not auth_required() or request.url.path in PUBLIC_PATHS:
        return {"sub": "anonymous"}

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Bearer token required"})

    token = header[7:].strip()
    secret = os.getenv("COGNIX_JWT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail={"code": "AUTH_NOT_CONFIGURED", "message": "Authentication is enabled but JWT verification is not configured"})

    options = {"verify_signature": True, "verify_exp": True}
    kwargs: dict[str, object] = {}

    issuer = os.getenv("COGNIX_JWT_ISSUER", "").strip()
    audience = os.getenv("COGNIX_JWT_AUDIENCE", "").strip()
    if issuer:
        kwargs["issuer"] = issuer
    if audience:
        kwargs["audience"] = audience
    elif not issuer:
        options["verify_aud"] = False

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options=options,
            **kwargs,
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Invalid or expired bearer token"})

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Token subject is required"})

    return claims
