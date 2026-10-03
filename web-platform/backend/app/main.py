import json
import os
import time
import logging
import re
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pythonjsonlogger import jsonlogger

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from app.auth import auth_required, authenticate_request
from app.routers import activity, brain_advanced, brain_agent, brain_documents, brain_media, brain_vault, exports, integrations, intelligence, level_up, processing, reviews, sources, usage
from app.store import store

API_VERSION = "1.0.0"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)
logger = logging.getLogger("cognix")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(os.getenv("COGNIX_LOG_LEVEL", "INFO"))
    logger.propagate = False

_SENSITIVE_QUERY = re.compile(r"(?i)(token|access_token|refresh_token|code|secret|key|password)=([^&]+)")


def _safe_request_path(request: Request) -> str:
    path = request.url.path[:500]
    query = _SENSITIVE_QUERY.sub(r"\1=[REDACTED]", request.url.query[:500])
    return f"{path}?{query}" if query else path
RATE_LIMIT = int(os.getenv("COGNIX_RATE_LIMIT_PER_MINUTE", "120"))
def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


COGNIX_ENV = os.getenv("COGNIX_ENV", "").strip().lower()
REQUIRE_DATABASE = _env_flag("COGNIX_REQUIRE_DATABASE", "true" if COGNIX_ENV == "production" else "false")
RATE_LIMIT_MAX_IDENTITIES = int(os.getenv("COGNIX_RATE_LIMIT_MAX_IDENTITIES", "10000"))
_rate_windows: dict[str, deque[float]] = defaultdict(deque)


def _cors_origins() -> list[str]:
    raw = os.getenv("COGNIX_CORS_ORIGINS", "").strip()
    configured = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if os.getenv("COGNIX_ENV", "").strip().lower() == "production":
        if not configured:
            raise RuntimeError("COGNIX_CORS_ORIGINS is required in production")
        if "*" in configured:
            raise RuntimeError("Wildcard CORS origin is not allowed in production")
    return configured or list(DEFAULT_CORS_ORIGINS)


if sentry_sdk and os.getenv("SENTRY_DSN", "").strip():
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
    )

app = FastAPI(
    title="Cognix Nexus API",
    version=API_VERSION,
    description="Research intelligence and personal knowledge OS API for Cognix Nexus.",
)


@app.on_event("startup")
def validate_production_configuration() -> None:
    environment = os.getenv("COGNIX_ENV", "").strip().lower()
    if environment == "production":
        if not os.getenv("DATABASE_URL", "").strip():
            raise RuntimeError("DATABASE_URL must be set in production")
        if not auth_required():
            raise RuntimeError("Authentication must be enabled in production; set COGNIX_AUTH_REQUIRED=true")
    if store.database is not None:
        try:
            store.initialize()
        except Exception as exc:
            raise RuntimeError("Failed to initialize database") from exc


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if sentry_sdk:
        sentry_sdk.capture_exception(exc)
    logger.error(
        "Unhandled request",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": _safe_request_path(request),
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        request.state.auth = authenticate_request(request)
        response = await call_next(request)
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        else:
            raise
    response.headers["x-request-id"] = request_id

    # Best-effort request telemetry. Never let observability failure break a request.
    if store.database is not None:
        try:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            with store.database.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO observability_events(event_type,request_id,duration_ms,metadata) "
                        "VALUES(%s,%s,%s,%s::jsonb)",
                        (
                            "http.request",
                            request_id,
                            duration_ms,
                            json.dumps({
                                "method": request.method,
                                "path": _safe_request_path(request),
                                "status_code": response.status_code,
                            }),
                        ),
                    )
                conn.commit()
        except Exception:
            pass
    return response



@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
    response.headers["permissions-policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if RATE_LIMIT > 0 and request.url.path not in {"/", "/health", "/ready"}:
        identity = request.headers.get("authorization", "")[:80] or (request.client.host if request.client else "unknown")
        now = time.monotonic()
        window = _rate_windows[identity]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= RATE_LIMIT:
            response = JSONResponse(
                status_code=429,
                content={"detail": {"code": "RATE_LIMITED", "message": "Too many requests"}},
                headers={"Retry-After": "60"},
            )
            response.headers["x-request-id"] = getattr(request.state, "request_id", str(uuid4()))
            return response
        window.append(now)
        if len(_rate_windows) > RATE_LIMIT_MAX_IDENTITIES:
            oldest = min(_rate_windows.items(), key=lambda item: item[1][-1] if item[1] else now)[0]
            if oldest != identity:
                _rate_windows.pop(oldest, None)
    return await call_next(request)

allowed_hosts = [host.strip() for host in os.getenv("COGNIX_ALLOWED_HOSTS", "").split(",") if host.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

_cors_allowed_origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins,
    allow_credentials=bool(_cors_allowed_origins),
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


def _register_api_routes(target):
    target.include_router(sources.router, prefix="/sources", tags=["sources"])
    target.include_router(brain_vault.router)
    target.include_router(brain_documents.router)
    target.include_router(brain_media.router)
    target.include_router(brain_advanced.router)
    target.include_router(brain_agent.router)
    target.include_router(intelligence.router)
    target.include_router(level_up.router)
    target.include_router(processing.router, prefix="/processing", tags=["processing"])
    target.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
    target.include_router(exports.router, prefix="/exports", tags=["exports"])
    target.include_router(activity.router, prefix="/activity", tags=["activity"])
    target.include_router(usage.router, prefix="/usage", tags=["usage"])
    target.include_router(integrations.router)


_register_api_routes(app)

v1_app = FastAPI(
    title="Cognix Nexus API v1",
    version="1.0.0",
    description="Versioned Cognix Nexus API.",
)
_register_api_routes(v1_app)
app.mount("/v1", v1_app)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "cognix-nexus-api", "version": API_VERSION, "docs": "/v1/docs", "openapi": "/v1/openapi.json"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cognix-nexus-api", "version": API_VERSION}


@app.get("/ready")
def readiness() -> dict[str, object]:
    database_configured = store.database is not None
    database_reachable = False
    if store.database:
        try:
            database_reachable = bool(store.database.ping())
        except Exception:
            database_reachable = False
    ready = (database_configured or not REQUIRE_DATABASE) and (not database_configured or database_reachable)
    return {
        "status": "ready" if ready else "not_ready",
        "service": "cognix-nexus-api",
        "version": API_VERSION,
        "database_configured": database_configured,
        "database_reachable": database_reachable,
        "persistence_mode": store.persistence_mode,
        "database_required": REQUIRE_DATABASE,
    }
