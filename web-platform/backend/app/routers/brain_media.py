from __future__ import annotations

from hashlib import sha256
import os
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document_ocr import extract_ocr
from app.services.object_storage import r2_storage
from app.store import store

router = APIRouter(prefix="/brain/media", tags=["brain-media"])

MAX_MEDIA_BYTES = 20 * 1024 * 1024
IMAGE_TYPES = {"png", "jpg", "jpeg", "webp", "tiff", "bmp"}


@router.post("/ingest", status_code=201)
async def ingest_media(file: UploadFile = File(...), ocr_language: str = "eng") -> dict:
    filename = file.filename or "media"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Vizora media ingestion currently accepts image files only")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Media file is empty")
    if len(data) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail="Media file exceeds the 20 MB limit")
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for media ingestion")

    media_id = f"MEDIA-{uuid4().hex[:8].upper()}"
    content_hash = sha256(data).hexdigest()
    try:
        pages = extract_ocr(data, suffix, language=ocr_language, max_pages=1)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Media OCR failed: {exc}") from exc
    text = pages[0].text if pages else ""

    storage_provider = os.getenv("COGNIX_MEDIA_STORAGE_PROVIDER", "local").strip().lower()
    binary_path = None
    if storage_provider == "r2":
        try:
            content_type = "image/jpeg" if suffix in {"jpg", "jpeg"} else f"image/{suffix}"
            binary_path = r2_storage().put_bytes(f"media/{media_id}/{filename}", data, content_type=content_type).key
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Media object storage failed: {type(exc).__name__}") from exc
    elif storage_provider != "local":
        raise HTTPException(status_code=503, detail="Unsupported media storage provider")

    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO media_assets(id,filename,media_type,content_hash,metadata,binary_storage,binary_path,binary_sha256) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                (media_id, filename, suffix, content_hash, {"ocr_language": ocr_language, "ocr_text_length": len(text)}, storage_provider, binary_path, content_hash),
            )
        conn.commit()
    return {
        "id": media_id,
        "filename": filename,
        "media_type": suffix,
        "content_hash": content_hash,
        "ocr_text": text,
        "message": "Media is normalized into the Brain Vault input boundary; richer visual understanding can be attached through a configured vision provider later.",
    }
