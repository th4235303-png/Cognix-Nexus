from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.google_drive import authorization_url, exchange_code, google_configured

router = APIRouter(prefix="/integrations/google-drive", tags=["integrations"])


@router.get("/authorize")
def authorize() -> dict[str, str]:
    if not google_configured():
        try:
            return {"authorization_url": authorization_url()}
        except Exception as exc:
            raise HTTPException(status_code=503, detail={"code": "GOOGLE_OAUTH_NOT_CONFIGURED", "message": str(exc)}) from exc
    return {"status": "configured", "message": "Google Drive credentials are already configured"}


@router.get("/callback", response_class=HTMLResponse)
def callback(code: str) -> str:
    try:
        tokens = exchange_code(code)
    except Exception as exc:
        raise HTTPException(status_code=502, detail={"code": "GOOGLE_OAUTH_FAILED", "message": str(exc)}) from exc
    return (
        "<h2>Cognix Core Google Drive authorization complete</h2>"
        "<p>Store the refresh token below in the backend secret manager, then remove it from this page/history.</p>"
        f"<pre>{tokens['refresh_token']}</pre>"
    )
