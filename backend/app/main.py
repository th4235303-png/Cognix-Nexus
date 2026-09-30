import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from app.auth import authenticate_request
from app.routers import activity, exports, processing, reviews, sources, usage
from app.store import store

API_VERSION = "0.1.0"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


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
    description="Research processing, review, and approved knowledge export API.",
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(processing.router, prefix="/processing", tags=["processing"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(activity.router, prefix="/activity", tags=["activity"])
app.include_router(usage.router, prefix="/usage", tags=["usage"])


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "cognix-core-api", "version": API_VERSION, "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cognix-core-api", "version": API_VERSION}


@app.get("/ready")
def readiness() -> dict[str, object]:
    database_configured = store.database is not None
    database_reachable = store.database.ping() if store.database else False
    ready = not database_configured or database_reachable
    return {
        "status": "ready" if ready else "not_ready",
        "service": "cognix-core-api",
        "version": API_VERSION,
        "database_configured": database_configured,
        "database_reachable": database_reachable,
        "persistence_mode": store.persistence_mode,
    }
