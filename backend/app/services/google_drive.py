"""Google Drive OAuth and export boundary."""
from __future__ import annotations

import os
from dataclasses import dataclass

from app.services.google_drive_package import build_file_contents

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

@dataclass
class ExportPackage:
    source_id: str
    folder: str
    files: tuple[str, ...]

def build_export_package(source_id: str, date: str) -> ExportPackage:
    return ExportPackage(source_id, f"/cognix-core/{date}/{source_id}/", ("source.json", "original-reference.txt", "summary.md", "myanmar-summary.md", "claims.json", "review.json"))

def google_configured() -> bool:
    return all(os.getenv(name, "").strip() for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_REFRESH_TOKEN"))

def authorization_url() -> str:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config({"web": {"client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"], "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": [os.environ["GOOGLE_REDIRECT_URI"]]}}, scopes=SCOPES)
    flow.redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
    return flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")[0]

def exchange_code(code: str) -> dict[str, str]:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config({"web": {"client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"], "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "redirect_uris": [os.environ["GOOGLE_REDIRECT_URI"]]}}, scopes=SCOPES)
    flow.redirect_uri = os.environ["GOOGLE_REDIRECT_URI"]
    flow.fetch_token(code=code)
    if not flow.credentials.refresh_token:
        raise RuntimeError("Google did not return a refresh token; revoke consent and authorize again")
    return {"refresh_token": flow.credentials.refresh_token, "scopes": " ".join(SCOPES)}

def upload_export(source: dict, package: ExportPackage) -> str:
    provider = os.getenv("COGNIX_DRIVE_PROVIDER", "mock").strip().lower()
    if provider == "mock":
        return f"mock-drive://cognix-core/{source['id']}"
    if provider != "google" or not google_configured():
        raise RuntimeError("Google Drive OAuth is not configured")
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload
    credentials = Credentials(token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token", client_id=os.environ["GOOGLE_CLIENT_ID"], client_secret=os.environ["GOOGLE_CLIENT_SECRET"], scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    root_id = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", "").strip() or None
    folder_id = _find_or_create_folder(service, source["id"], root_id)
    for name, (content, mime_type) in build_file_contents(source).items():
        metadata = {"name": name, "parents": [folder_id]}
        media = MediaInMemoryUpload(content.encode("utf-8"), mimetype=mime_type, resumable=False)
        safe_name = name.replace("'", "\\'")
        found = service.files().list(q=f"name = '{safe_name}' and '{folder_id}' in parents and trashed = false", fields="files(id)", pageSize=1).execute().get("files", [])
        if found:
            service.files().update(fileId=found[0]["id"], media_body=media).execute()
        else:
            service.files().create(body=metadata, media_body=media, fields="id").execute()
    return f"gdrive://folder/{folder_id}"

def _find_or_create_folder(service, name: str, parent_id: str | None) -> str:
    escaped = name.replace("'", "\\'")
    query = f"name = '{escaped}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    found = service.files().list(q=query, fields="files(id)", pageSize=1).execute().get("files", [])
    if found:
        return found[0]["id"]
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    return service.files().create(body=body, fields="id").execute()["id"]
