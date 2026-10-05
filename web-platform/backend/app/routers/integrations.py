import html
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.google_drive import authorization_url, exchange_code, google_configured, verify_oauth_state
from app.services.object_storage import b2_storage, cloudinary_storage, r2_storage, supabase_storage

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
def callback(code: str, state: str) -> str:
    if not verify_oauth_state(state):
        raise HTTPException(status_code=400, detail={"code": "GOOGLE_OAUTH_STATE_INVALID", "message": "OAuth state is invalid or expired"})
    try:
        result = exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "GOOGLE_OAUTH_FAILED", "message": type(exc).__name__}) from exc
    token = result["refresh_token"]
    return (
        "<h2>Cognix Core Google Drive authorization complete</h2>"
        "<p>Copy the refresh token below into the server secret "
        "<code>GOOGLE_REFRESH_TOKEN</code>. Do not commit or share it.</p>"
        f"<textarea readonly rows='6' cols='100'>{html.escape(token)}</textarea>"
    )


@router.get("/storage/status")
def storage_status() -> dict:
    return {
        "book_storage_provider": os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower(),
        "media_storage_provider": os.getenv("COGNIX_MEDIA_STORAGE_PROVIDER", "local").strip().lower(),
        "cloudinary_configured": cloudinary_storage().configured,
        "b2_configured": b2_storage().configured,
        "supabase_storage_configured": supabase_storage().configured,
        "r2_configured": r2_storage().configured,
        "google_drive_configured": google_configured(),
        "roles": {
            "primary_originals": os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower(),
            "media_originals": os.getenv("COGNIX_MEDIA_STORAGE_PROVIDER", "local").strip().lower(),
            "app_artifacts": "supabase_storage",
            "exports_and_backup": "google_drive",
        },
    }
