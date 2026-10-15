from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.document_ocr import extract_ocr
from app.store import store

router = APIRouter(prefix="/brain/documents", tags=["brain-documents"])

MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
ALLOWED_TYPES = {"pdf", "png", "jpg", "jpeg", "webp", "tiff", "bmp"}


class OCRRequest(BaseModel):
    language: str = Field(default="eng", min_length=2, max_length=32)
    max_pages: int = Field(default=50, ge=1, le=50)


@router.post("/ocr", status_code=201)
async def ocr_document(
    file: UploadFile = File(...),
    language: str = "eng",
    max_pages: int = 50,
) -> dict:
    filename = file.filename or "document"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported OCR file type")
    if not 1 <= max_pages <= 50:
        raise HTTPException(status_code=400, detail="max_pages must be between 1 and 50")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 20 MB OCR limit")

    job_id = f"DOC-{uuid4().hex[:8].upper()}"
    content_hash = sha256(data).hexdigest()
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for OCR jobs")

    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO document_jobs(id,filename,file_type,status,content_hash) VALUES(%s,%s,%s,%s,%s)",
                (job_id, filename, suffix, "processing", content_hash),
            )
        conn.commit()

    try:
        pages = extract_ocr(data, suffix, language=language, max_pages=max_pages)
        result = {
            "filename": filename,
            "file_type": suffix,
            "content_hash": content_hash,
            "language": language,
            "pages": [{"page_number": page.page_number, "text": page.text} for page in pages],
            "text": "\n\n".join(page.text for page in pages if page.text),
        }
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE document_jobs SET status=%s,result=%s,updated_at=now() WHERE id=%s",
                    ("completed", result, job_id),
                )
            conn.commit()
        return {"job_id": job_id, "status": "completed", **result}
    except Exception as exc:
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE document_jobs SET status=%s,error=%s,updated_at=now() WHERE id=%s",
                    ("failed", str(exc), job_id),
                )
            conn.commit()
        raise HTTPException(status_code=503, detail=f"OCR processing failed: {exc}") from exc


@router.get("/{job_id}")
def get_ocr_job(job_id: str) -> dict:
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for OCR jobs")
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM document_jobs WHERE id=%s", (job_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document job not found")
    return row
