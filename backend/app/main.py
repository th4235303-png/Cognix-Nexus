import os
from uuid import uuid4

from fastapi import FastAPI, Request\nfrom fastapi.responses import JSONResponse\n\nfrom app.auth import authenticate_request
from fastapi.middleware.cors import CORSMiddleware

from app.routers import activity, exports, processing, reviews, sources, usage
from app.store import store

API_VERSION = "0.1.0"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


def _cors_origins() -> list[str]:
    raw = os.getenv("COGNIX_CORS_ORIGINS", "")
    configured = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return configured or list(DEFAULT_CORS_ORIGINS)


app = FastAPI(
    title="Cognix Core API",
    version=API_VERSION,
    description="Research processing, review, and approved knowledge export API.",
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
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
    return {
        "service": "cognix-core-api",
        "version": API_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cognix-core-api", "version": API_VERSION}


@app.get("/ready")
def readiness() -> dict[str, object]:
    database_configured = store.database is not None
    return {
        "status": "ready",
        "service": "cognix-core-api",
        "version": API_VERSION,
        "database_configured": database_configured,
        "persistence_mode": store.persistence_mode,
    }
