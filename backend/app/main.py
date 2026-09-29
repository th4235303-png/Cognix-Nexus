from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import activity, exports, processing, reviews, sources, usage

app = FastAPI(title="Cognix Core API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cognix-core-api"}
