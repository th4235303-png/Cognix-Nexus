import os
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from app.auth import authenticate_request
from app.routers import activity, brain_advanced, brain_documents, brain_media, brain_vault, exports, integrations, processing, reviews, sources, usage
from app.store import store

API_VERSION = "0.1.0"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)
RATE_LIMIT = int(os.getenv("COGNIX_RATE_LIMIT_PER_MINUTE", "120"))
REQUIRE_DATABASE = os.getenv("COGNIX_REQUIRE_DATABASE", "false").strip().lower() in {"1", "true", "yes", "on"}
RATE_LIMIT_MAX_IDENTITIES = int(os.getenv("COGNIX_RATE_LIMIT_MAX_IDENTITIES", "10000"))
_rate_windows: dict[str, deque[float]] = defaultdict(deque)


def _cors_origins() -> list[str]:
    raw = os.getenv("COGNIX_CORS_ORIGINS", "")
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return configured or list(DEFAULT_CORS_ORIGINS)


if sentry_sdk and os.getenv("SENTRY_DSN", "").strip():
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
    )

app = FastAPI(
    title="Cognix Core API",
    version=API_VERSION,
    description="Research intelligence and personal knowledge OS API.",
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(brain_vault.router)
app.include_router(brain_documents.router)
app.include_router(brain_media.router)
app.include_router(brain_advanced.router)
app.include_router(processing.router, prefix="/processing", tags=["processing"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(activity.router, prefix="/activity", tags=["activity"])
app.include_router(usage.router, prefix="/usage", tags=["usage"])
app.include_router(integrations.router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "cognix-core-api", "version": API_VERSION, "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cognix-core-api", "version": API_VERSION}


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
        "service": "cognix-core-api",
        "version": API_VERSION,
        "database_configured": database_configured,
        "database_reachable": database_reachable,
        "persistence_mode": store.persistence_mode,
        "database_required": REQUIRE_DATABASE,
    }
