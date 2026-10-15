from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import os
import re
import zipfile
import xml.etree.ElementTree as ET

from pypdf import PdfReader


@dataclass
class ExtractedDocument:
    title: str
    author: str | None
    file_type: str
    text: str
    sections: list[dict]


def _clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def extract_pdf(data: bytes, filename: str) -> ExtractedDocument:
    reader = PdfReader(BytesIO(data))
    pages = []
    ocr_enabled = os.getenv("COGNIX_BOOK_OCR_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    ocr_language = os.getenv("COGNIX_BOOK_OCR_LANGUAGE", "eng+mya").strip() or "eng"
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if not text and ocr_enabled:
            try:
                import fitz
                from PIL import Image
                import pytesseract
                pdf = fitz.open(stream=data, filetype="pdf")
                try:
                    rendered = pdf[index - 1].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
                    image = Image.open(BytesIO(rendered.tobytes("png"))).convert("RGB")
                    try:
                        text = _clean_text(pytesseract.image_to_string(image, lang=ocr_language, config="--psm 3"))
                    except Exception:
                        text = _clean_text(pytesseract.image_to_string(image, lang="eng", config="--psm 3"))
                finally:
                    pdf.close()
            except Exception:
                text = ""
        if text:
            pages.append({"page_number": index, "title": f"Page {index}", "text": text})
    text = "\n\n".join(item["text"] for item in pages)
    return ExtractedDocument(
        title=Path(filename).stem,
        author=None,
        file_type="pdf",
        text=text,
        sections=pages,
    )


def _epub_text_nodes(data: bytes) -> list[tuple[str, str]]:
    # EPUB is a ZIP container. We deliberately parse XHTML locally and do not
    # resolve remote URLs, avoiding SSRF through document ingestion.
    with zipfile.ZipFile(BytesIO(data)) as archive:
        names = archive.namelist()
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = next(
            (node.attrib.get("full-path") for node in container.iter()
             if node.tag.endswith("rootfile")),
            None,
        )
        if not rootfile:
            raise ValueError("EPUB container.xml has no rootfile")
        opf = ET.fromstring(archive.read(rootfile))
        base = str(Path(rootfile).parent)
        manifest = {
            item.attrib.get("id"): item.attrib.get("href")
            for item in opf.iter()
            if item.tag.endswith("item") and item.attrib.get("id") and item.attrib.get("href")
        }
        spine = [
            item.attrib.get("idref")
            for item in opf.iter()
            if item.tag.endswith("itemref") and item.attrib.get("idref")
        ]
        result = []
        for idref in spine:
            href = manifest.get(idref)
            if not href:
                continue
            path = str(Path(base) / href.split("#", 1)[0])
            path = path.replace("\\", "/")
            if path not in names:
                continue
            root = ET.fromstring(archive.read(path))
            parts = []
            for node in root.iter():
                if node.text:
                    parts.append(node.text)
                if node.tail:
                    parts.append(node.tail)
            result.append((Path(path).stem, _clean_text(" ".join(parts))))
        return result


def extract_epub(data: bytes, filename: str) -> ExtractedDocument:
    sections = [
        {"section_number": index, "title": title, "text": text}
        for index, (title, text) in enumerate(_epub_text_nodes(data), start=1)
        if text
    ]
    text = "\n\n".join(item["text"] for item in sections)
    return ExtractedDocument(
        title=Path(filename).stem,
        author=None,
        file_type="epub",
        text=text,
        sections=sections,
    )


def extract_text(data: bytes, filename: str) -> ExtractedDocument:
    text = _clean_text(data.decode("utf-8", errors="replace"))
    sections = [{"section_number": 1, "title": "Imported Text", "text": text}] if text else []
    return ExtractedDocument(title=Path(filename).stem, author=None, file_type="txt", text=text, sections=sections)


def extract_docx(data: bytes, filename: str) -> ExtractedDocument:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for node in root.iter():
        if node.tag.endswith("}p"):
            value = "".join(part.text or "" for part in node.iter() if part.tag.endswith("}t"))
            if value.strip():
                paragraphs.append(_clean_text(value))
    text = "\n\n".join(paragraphs)
    sections = [{"section_number": i, "title": f"Paragraph {i}", "text": value} for i, value in enumerate(paragraphs, 1)]
    return ExtractedDocument(title=Path(filename).stem, author=None, file_type="docx", text=text, sections=sections)


def extract_document(data: bytes, filename: str, file_type: str | None = None) -> ExtractedDocument:
    suffix = (file_type or Path(filename).suffix.lstrip(".")).lower()
    if suffix == "pdf":
        return extract_pdf(data, filename)
    if suffix == "epub":
        return extract_epub(data, filename)
    if suffix == "txt":
        return extract_text(data, filename)
    if suffix == "docx":
        return extract_docx(data, filename)
    raise ValueError("Only PDF, EPUB, DOCX and TXT uploads are supported")
