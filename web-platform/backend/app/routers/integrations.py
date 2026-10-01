import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.google_drive import authorization_url, exchange_code, google_configured
from app.services.object_storage import r2_storage

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google-drive/authorize")
def authorize() -> dict[str, str]:
    if google_configured():
        return {"status": "configured", "message": "Google Drive credentials are already configured"}
    try:
        return {"authorization_url": authorization_url()}
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "GOOGLE_OAUTH_NOT_CONFIGURED", "message": str(exc)}) from exc


@router.get("/google-drive/callback", response_class=HTMLResponse)
def callback(code: str) -> str:
    try:
        exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "GOOGLE_OAUTH_FAILED", "message": str(exc)}) from exc
    return (
        "<h2>Cognix Core Google Drive authorization complete</h2>"
        "<p>Authorization succeeded. The refresh token is intentionally not displayed in the browser.</p>"
        "<p>Store the credential through your backend secret-management process as GOOGLE_REFRESH_TOKEN, then reload the API.</p>"
    )


@router.get("/storage/status")
def storage_status() -> dict:
    r2 = r2_storage()
    return {
        "book_storage_provider": __import__("os").getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower(),
        "media_storage_provider": __import__("os").getenv("COGNIX_MEDIA_STORAGE_PROVIDER", "local").strip().lower(),
        "r2_configured": r2.configured,
        "google_drive_configured": google_configured(),
    }
