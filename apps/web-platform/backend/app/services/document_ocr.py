from __future__ import annotations

import io
import os
from dataclasses import dataclass

from PIL import Image
import pytesseract


@dataclass(frozen=True)
class OCRPage:
    page_number: int
    text: str


def _ocr_image(image: Image.Image, language: str) -> str:
    config = os.getenv("COGNIX_OCR_TESSERACT_CONFIG", "--psm 3")
    return pytesseract.image_to_string(image, lang=language, config=config).strip()


def extract_ocr(data: bytes, file_type: str, language: str = "eng", max_pages: int = 50) -> list[OCRPage]:
    """Extract OCR text from common images or rendered PDF pages.

    Tesseract language packs are deployment-level dependencies. The API returns
    a clear 503 when the requested pack/binary is unavailable rather than
    silently returning empty text.
    """
    kind = file_type.lower()
    if kind == "pdf":
        try:
            import fitz
            document = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise RuntimeError(f"PDF rendering is unavailable: {exc}") from exc
        pages: list[OCRPage] = []
        try:
            for index, page in enumerate(document, start=1):
                if index > max_pages:
                    break
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
                image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
                pages.append(OCRPage(index, _ocr_image(image, language)))
        finally:
            document.close()
        return pages

    if kind in {"png", "jpg", "jpeg", "webp", "tiff", "bmp"}:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        return [OCRPage(1, _ocr_image(image, language))]

    raise ValueError("Unsupported OCR file type")
