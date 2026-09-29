import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import activity, exports, processing, reviews, sources, usage

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
