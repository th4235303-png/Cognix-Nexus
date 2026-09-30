from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
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
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
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


def extract_document(data: bytes, filename: str, file_type: str | None = None) -> ExtractedDocument:
    suffix = (file_type or Path(filename).suffix.lstrip(".")).lower()
    if suffix == "pdf":
        return extract_pdf(data, filename)
    if suffix == "epub":
        return extract_epub(data, filename)
    raise ValueError("Only PDF and EPUB uploads are supported")
