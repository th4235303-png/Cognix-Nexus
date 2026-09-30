from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.google_drive import authorization_url, exchange_code, google_configured
router = APIRouter(prefix="/integrations/google-drive", tags=["integrations"])
@router.get("/authorize")
def authorize() -> dict[str,str]:
    if google_configured(): return {"status":"configured","message":"Google Drive credentials are already configured"}
    try: return {"authorization_url":authorization_url()}
    except Exception as exc: raise HTTPException(status_code=503,detail={"code":"GOOGLE_OAUTH_NOT_CONFIGURED","message":str(exc)}) from exc
@router.get("/callback", response_class=HTMLResponse)
def callback(code: str) -> str:
    try: exchange_code(code)
    except Exception as exc: raise HTTPException(status_code=502,detail={"code":"GOOGLE_OAUTH_FAILED","message":str(exc)}) from exc
    return "<h2>Cognix Core Google Drive authorization complete</h2><p>Authorization succeeded. The refresh token is intentionally not displayed in the browser.</p><p>Store the credential through your backend secret-management process as GOOGLE_REFRESH_TOKEN, then reload the API.</p>"
